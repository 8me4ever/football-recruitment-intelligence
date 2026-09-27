$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$snapshotDir = Join-Path $projectRoot 'data\csl\decision_snapshot_2026-09-27'
$decisionDate = [datetime]::ParseExact('2026-09-27', 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
$profilePath = Join-Path $snapshotDir 'player_public_profile_evidence_2026_guoan.csv'
$cohortPath = Join-Path $snapshotDir 'c2_operational_cohort_2026-09-27.csv'
$participationPath = Join-Path $snapshotDir 'player_match_participation_2026_guoan.csv'
$sourcePath = Join-Path $snapshotDir 'public_source_register.csv'

$wikiId = 'wikipedia_guoan_2026_squad_profile_2026-09-14'
$nftId = 'national_football_teams_guoan_2026_roster_profiles'
$cfaId = 'cfa_youth_athlete_registration_lu_tongyun_2023'
$wikiUrl = 'https://zh.wikipedia.org/wiki/北京国安足球俱乐部2026赛季'
$nftUrl = 'https://www.national-football-teams.com/club/437/2026_2/Beijing_Guoan.html'
$cfaUrl = 'https://imageoss.thecfa.cn/upload/file/20230628/1687936794968511.pdf'

$sourceRows = @(Import-Csv -LiteralPath $sourcePath)
$sourceMap = @{}
foreach ($row in $sourceRows) { $sourceMap[$row.source_id] = $row }
$newSources = @(
    [pscustomobject]@{
        evidence_note = '2026 season article first-team roster table is marked updated 2026-09-14 and lists player birth dates and position labels. Used for profile evidence only, not to establish decision-date squad membership.'
        published_at = '2026-09-14'
        source_id = $wikiId
        source_type = 'secondary_compiled_squad_profile'
        transcription_url = ''
        url = $wikiUrl
    },
    [pscustomobject]@{
        evidence_note = '2026 Beijing Guoan page lists dates of birth and detailed position labels for 18 players cross-checked here. Secondary profile database; it does not define the project squad cohort.'
        published_at = ''
        source_id = $nftId
        source_type = 'secondary_player_profile_database'
        transcription_url = ''
        url = $nftUrl
    },
    [pscustomobject]@{
        evidence_note = 'Chinese Football Association public youth-athlete register row 45 lists Lu Tongjun with date of birth 2008-03-30; the identifier is partially redacted.'
        published_at = '2023-06-28'
        source_id = $cfaId
        source_type = 'official_cfa_youth_athlete_registration_list'
        transcription_url = ''
        url = $cfaUrl
    }
)
foreach ($source in $newSources) {
    if (-not $sourceMap.ContainsKey($source.source_id)) {
        $sourceMap[$source.source_id] = $source
    }
}

$cohortRows = @(Import-Csv -LiteralPath $cohortPath)
$profileRows = @(Import-Csv -LiteralPath $profilePath)
$participationRows = @(Import-Csv -LiteralPath $participationPath)
$cohortByKey = @{}
$profileByKey = @{}
foreach ($row in $cohortRows) {
    if ($cohortByKey.ContainsKey($row.player_key)) { throw "Duplicate cohort player_key: $($row.player_key)" }
    $cohortByKey[$row.player_key] = $row
}
foreach ($row in $profileRows) {
    if ($profileByKey.ContainsKey($row.player_key)) { throw "Duplicate evidence player_key: $($row.player_key)" }
    $profileByKey[$row.player_key] = $row
}
if ($cohortRows.Count -ne $profileRows.Count) { throw 'C2 cohort and profile evidence row counts differ.' }

$specificZh = @('中后卫','边后卫','后腰','中前卫','前腰','边锋')
$broadZh = @('守门员','后卫','中场','前锋')
$ageRows = foreach ($member in $cohortRows) {
    $profile = $profileByKey[$member.player_key]
    if ($null -eq $profile) { throw "Missing profile evidence for $($member.player_key)" }
    if ($profile.player_name_zh -ne $member.player_name_zh) { throw "Name mismatch for $($member.player_key)" }
    if ($profile.player_id -ne $member.player_id) { throw "ID mismatch for $($member.player_key)" }
    if ([string]::IsNullOrWhiteSpace($profile.date_of_birth)) { throw "Missing DOB for $($member.player_key)" }
    if (-not $sourceMap.ContainsKey($profile.birth_date_source_id)) { throw "Unregistered DOB source for $($member.player_key)" }
    $birthDate = [datetime]::ParseExact($profile.date_of_birth, 'yyyy-MM-dd', [Globalization.CultureInfo]::InvariantCulture)
    $age = $decisionDate.Year - $birthDate.Year
    if ([int]$decisionDate.ToString('MMdd') -lt [int]$birthDate.ToString('MMdd')) { $age-- }
    $ageBand = if ($age -le 21) { '21岁及以下' } elseif ($age -le 24) { '22–24岁' } elseif ($age -le 29) { '25–29岁' } else { '30岁及以上' }
    $birthSource = $sourceMap[$profile.birth_date_source_id]
    $birthStatus = if ($profile.birth_date_source_id -eq $cfaId -and $profile.birth_date_crosscheck_source_id) {
        'official_registration_date_crosschecked_by_secondary_database'
    } elseif ($profile.birth_date_crosscheck_source_id) {
        'dob_crosschecked_by_secondary_database'
    } elseif ($profile.birth_date_source_id -eq $cfaId) {
        'official_registration_date'
    } else {
        'single_secondary_profile_source'
    }
    $positionStatus = if (($specificZh -contains $profile.public_position_label_zh) -or
        ($profile.public_position_label_en_secondary -and $profile.public_position_label_en_secondary -ne 'Goalkeeper')) {
        'has_specific_public_position_label'
    } elseif (($broadZh -contains $profile.public_position_label_zh) -or
        ($profile.public_position_label_en_secondary -eq 'Goalkeeper')) {
        'broad_position_group_only'
    } else {
        'no_profile_position_label'
    }
    $positionUrl = ''
    if ($profile.public_position_source_id) {
        if (-not $sourceMap.ContainsKey($profile.public_position_source_id)) { throw "Unregistered position source for $($member.player_key)" }
        $positionUrl = $sourceMap[$profile.public_position_source_id].url
    }
    $playerRoleRows = @($participationRows | Where-Object { $_.player_id -eq $member.player_id -and -not [string]::IsNullOrWhiteSpace($_.observed_role) })
    $roleFixtureCount = @($playerRoleRows | Select-Object -ExpandProperty event_id -Unique).Count
    $roleStatus = if ($roleFixtureCount -gt 1) { 'match_specific_role_evidence_multiple_fixtures' } elseif ($roleFixtureCount -eq 1) { 'match_specific_role_evidence_one_fixture' } else { 'unknown_match_deployment_role' }
    [pscustomobject][ordered]@{
        decision_date = $decisionDate.ToString('yyyy-MM-dd')
        player_key = $member.player_key
        player_id = $member.player_id
        player_name_zh = $member.player_name_zh
        registration_nominal_position = $member.nominal_position
        date_of_birth = $profile.date_of_birth
        age_years_on_decision_date = $age
        age_band = $ageBand
        birth_date_source_id = $profile.birth_date_source_id
        birth_date_source_url = $birthSource.url
        birth_date_source_tier = $birthSource.source_type
        birth_date_source_locator = $profile.birth_date_locator
        birth_date_verification_status = $birthStatus
        birth_date_crosscheck_source_id = $profile.birth_date_crosscheck_source_id
        public_position_label_zh = $profile.public_position_label_zh
        public_position_source_id = $profile.public_position_source_id
        public_position_source_url = $positionUrl
        public_position_source_locator = $profile.public_position_locator
        public_position_label_en_secondary = $profile.public_position_label_en_secondary
        public_position_crosscheck_source_id = $profile.public_position_crosscheck_source_id
        public_position_evidence_status = $positionStatus
        stats_sample_status = $member.stats_sample_status
        season_stats_appearances = $member.season_stats_appearances
        season_minutes_sum_from_displayed_minutes = $member.season_minutes_sum_from_displayed_minutes
        source_supported_starts_count_partial = $member.source_supported_starts_count_partial
        observed_position_groups = $member.observed_position_groups
        observed_role_status = $roleStatus
    }
}
$ageRows = @($ageRows | Sort-Object registration_nominal_position,player_name_zh)

$bandNames = @('21岁及以下','22–24岁','25–29岁','30岁及以上')
$allAges = @($ageRows | ForEach-Object { [int]$_.age_years_on_decision_date })
$ageBandCounts = [ordered]@{}
foreach ($name in $bandNames) { $ageBandCounts[$name] = @($ageRows | Where-Object age_band -eq $name).Count }
$verificationCounts = [ordered]@{}
foreach ($name in @('dob_crosschecked_by_secondary_database','official_registration_date_crosschecked_by_secondary_database','official_registration_date','single_secondary_profile_source')) {
    $verificationCounts[$name] = @($ageRows | Where-Object birth_date_verification_status -eq $name).Count
}
$positionCounts = [ordered]@{}
foreach ($name in @('has_specific_public_position_label','broad_position_group_only','no_profile_position_label')) {
    $positionCounts[$name] = @($ageRows | Where-Object public_position_evidence_status -eq $name).Count
}
$positionSummary = [ordered]@{}
foreach ($position in @('Goalkeeper','Defender','Midfielder','Forward')) {
    $rows = @($ageRows | Where-Object registration_nominal_position -eq $position)
    $counts = [ordered]@{}
    foreach ($name in $bandNames) { $counts[$name] = @($rows | Where-Object age_band -eq $name).Count }
    $groupAges = @($rows | ForEach-Object { [int]$_.age_years_on_decision_date })
    $positionSummary[$position] = [ordered]@{
        players = $rows.Count
        mean_age_years = [math]::Round(($groupAges | Measure-Object -Average).Average, 1)
        median_age_years = @($groupAges | Sort-Object)[[math]::Floor($groupAges.Count / 2)]
        age_bands = $counts
        positive_minute_sample = @($rows | Where-Object stats_sample_status -eq 'observed_current_season_sample').Count
        no_stat_row = @($rows | Where-Object stats_sample_status -ne 'observed_current_season_sample').Count
    }
}
$knownRoles = @($participationRows | Where-Object { -not [string]::IsNullOrWhiteSpace($_.observed_role) }).Count
$summary = [ordered]@{
    decision_date = $decisionDate.ToString('yyyy-MM-dd')
    population = '39-person user-reconciled decision-date first-team cohort'
    players = $ageRows.Count
    birth_dates_present = @($ageRows | Where-Object date_of_birth).Count
    birth_date_verification = $verificationCounts
    mean_age_years = [math]::Round(($allAges | Measure-Object -Average).Average, 1)
    median_age_years = @($allAges | Sort-Object)[[math]::Floor($allAges.Count / 2)]
    minimum_age_years = ($allAges | Measure-Object -Minimum).Minimum
    maximum_age_years = ($allAges | Measure-Object -Maximum).Maximum
    age_band_counts = $ageBandCounts
    by_registration_nominal_position = $positionSummary
    public_position_label_evidence_counts = $positionCounts
    match_participation_rows = $participationRows.Count
    match_participation_rows_with_observed_role = $knownRoles
    caveat = 'Public profile positions are not match-specific roles. One ACL fixture has formation-line-only labels and one CSL fixture has only match-reported broad position groups; the CSL formation remains disputed. These two fixtures provide 22 role-tagged rows; the other 384 match rows remain unknown. G/D/M/F remains a broad match-stat position group.'
}
$ageTable = $ageRows |
    Select-Object decision_date,player_key,player_id,player_name_zh,registration_nominal_position,date_of_birth,age_years_on_decision_date,age_band,birth_date_source_id,birth_date_verification_status,public_position_label_zh,public_position_label_en_secondary,stats_sample_status,observed_role_status |
    ConvertTo-Csv -NoTypeInformation
$summary | Add-Member -NotePropertyName age_csv_output -NotePropertyValue $ageTable
$summary | ConvertTo-Json -Depth 8
