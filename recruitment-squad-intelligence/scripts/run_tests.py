"""
无依赖测试运行器（pytest 的极简替代）。

背景：目标环境（旧项目的 venv）未安装 pytest，且沙箱无法联网安装。
为了不因缺工具而放弃回归测试，这里实现一个只依赖标准库的收集与执行器，
支持本项目测试用到的三个 pytest 特性：
  - `@pytest.mark.parametrize`（通过内置 shim 的 pytest 模块提供）
  - `tmp_path` 夹具
  - `monkeypatch.setitem` 夹具

运行：
    python scripts/run_tests.py
"""
from __future__ import annotations

import inspect
import shutil
import sys
import tempfile
import traceback
from pathlib import Path
from types import ModuleType, SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


# --------------------------------------------------------------------------------------
# pytest shim：只实现本项目需要的部分
# --------------------------------------------------------------------------------------

class _Mark:
    @staticmethod
    def parametrize(argnames, argvalues):
        if isinstance(argnames, str):
            names = [a.strip() for a in argnames.split(",")]
        else:
            names = list(argnames)

        def deco(fn):
            cases = getattr(fn, "_parametrize_cases", [])
            cases = cases + [(tuple(names), list(argvalues))]
            fn._parametrize_cases = cases
            return fn

        return deco


class _PytestShim(ModuleType):
    def __init__(self) -> None:
        super().__init__("pytest")
        self.mark = _Mark()

    @staticmethod
    def approx(value, rel=1e-6, abs=1e-12):  # noqa: A002
        return _Approx(value, rel, abs)

    @staticmethod
    def raises(exc, match=None):
        return _Raises(exc, match)

    @staticmethod
    def fail(msg: str = "") -> None:
        raise AssertionError(msg)


class _Approx:
    def __init__(self, value, rel, abs_):  # noqa: A002
        self.value = value
        self.rel = rel
        self.abs = abs_

    def __eq__(self, other) -> bool:
        try:
            return abs(other - self.value) <= max(
                self.abs, self.rel * max(abs(other), abs(self.value))
            )
        except TypeError:
            return NotImplemented

    def __repr__(self) -> str:
        return f"approx({self.value!r})"


class _Raises:
    def __init__(self, exc, match):
        self.exc = exc
        self.match = match

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            raise AssertionError(f"未抛出预期异常 {self.exc.__name__}")
        if not issubclass(exc_type, self.exc):
            return False  # 让意外异常继续向上传播
        if self.match is not None:
            import re

            if not re.search(self.match, str(exc)):
                raise AssertionError(
                    f"异常信息不匹配 {self.match!r}，实际为 {str(exc)!r}"
                )
        return True


sys.modules["pytest"] = _PytestShim()


# --------------------------------------------------------------------------------------
# 夹具
# --------------------------------------------------------------------------------------

class _MonkeyPatch:
    def __init__(self) -> None:
        self._undo: list = []

    def setitem(self, dic, key, value) -> None:
        had = key in dic
        old = dic.get(key)
        dic[key] = value
        self._undo.append((dic, key, had, old))

    def setattr(self, obj, name, value) -> None:
        had = hasattr(obj, name)
        old = getattr(obj, name, None)
        setattr(obj, name, value)
        self._undo.append((obj, name, had, old))

    def undo(self) -> None:
        for target, key, had, old in reversed(self._undo):
            if isinstance(target, dict):
                if had:
                    target[key] = old
                else:
                    target.pop(key, None)
            else:
                if had:
                    setattr(target, key, old)
                else:
                    delattr(target, key)


def _build_args(fn, names_case):
    args = []
    kwargs = {}
    for pname in inspect.signature(fn).parameters:
        if pname == "tmp_path":
            d = Path(tempfile.mkdtemp(prefix="rsitest_"))
            args.append(d)
        elif pname == "monkeypatch":
            args.append(_MonkeyPatch())
        elif pname == "capsys":
            raise RuntimeError("capsys 夹具未在本运行器中实现")
    return args, kwargs


# --------------------------------------------------------------------------------------
# 收集与执行
# --------------------------------------------------------------------------------------

def discover() -> list[tuple[str, object, list]]:
    tests: list[tuple[str, object, list]] = []
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        modname = path.stem
        spec = __import__(f"tests.{modname}", fromlist=["*"])
        for name, obj in vars(spec).items():
            if not name.startswith("test_") or not callable(obj):
                continue
            cases = getattr(obj, "_parametrize_cases", None)
            if not cases:
                tests.append((f"{modname}::{name}", obj, [({}, "")]))
                continue

            # 展开所有 parametrize 的笛卡尔积（支持多层堆叠，如 season × category）
            combos: list[tuple[dict, str]] = [({}, "")]
            for names, values in cases:
                new_combos: list[tuple[dict, str]] = []
                for base_kw, base_label in combos:
                    for v in values:
                        kw = dict(base_kw)
                        if len(names) == 1:
                            kw[names[0]] = v
                            label = f"{base_label}[{v!r}]"
                        else:
                            kw.update(dict(zip(names, v)))
                            label = f"{base_label}[{v!r}]"
                        new_combos.append((kw, label))
                combos = new_combos
            tests.append((f"{modname}::{name}", obj, combos))
    return tests


def main() -> int:
    (ROOT / "tests" / "__init__.py").touch(exist_ok=True)
    try:
        tests = discover()
    except Exception:
        traceback.print_exc()
        return 2

    passed = failed = 0
    failures: list[str] = []

    for test_id, fn, cases in tests:
        for kw, label in cases:
            display = f"{test_id}{label}"
            sig = inspect.signature(fn)
            call_kwargs = dict(kw)
            extra_args, _ = _build_args(fn, None)
            # 按签名顺序装配位置参数（夹具）与关键字参数（parametrize）
            pos_args = [a for a in extra_args]
            mp = next((a for a in pos_args if isinstance(a, _MonkeyPatch)), None)
            try:
                fn(*pos_args, **call_kwargs)
                passed += 1
            except Exception as e:
                failed += 1
                tb = traceback.format_exc()
                failures.append(f"FAIL {display}\n{'-' * 70}\n{tb}")
            finally:
                if mp is not None:
                    mp.undo()

    print("=" * 92)
    print(f"通过 {passed} / 失败 {failed} / 合计 {passed + failed}")
    print("=" * 92)
    if failures:
        print()
        for f in failures:
            print(f)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
