$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$plugin = Join-Path $root "_review_unzip\astrbot_plugin_0721_mode"
$main = Join-Path $plugin "main.py"
$schema = Join-Path $plugin "_conf_schema.json"
$metadata = Join-Path $plugin "metadata.yaml"
$readme = Join-Path $plugin "README.md"
$requirements = Join-Path $plugin "requirements.txt"
$zip = Join-Path $root "astrbot_plugin_0721_mode.zip"

if (-not (Test-Path $main)) { throw "main.py not found: $main" }
if (-not (Test-Path $schema)) { throw "_conf_schema.json not found: $schema" }
if (-not (Test-Path $metadata)) { throw "metadata.yaml not found: $metadata" }

$mainText = Get-Content -Encoding UTF8 -Raw $main
$schemaText = Get-Content -Encoding UTF8 -Raw $schema
$metadataText = Get-Content -Encoding UTF8 -Raw $metadata

function Assert-Contains($Text, $Pattern, $Name) {
  if ($Text -notmatch $Pattern) {
    throw "FAIL: $Name"
  }
  Write-Host "PASS: $Name"
}

function Assert-NotContains($Text, $Pattern, $Name) {
  if ($Text -match $Pattern) {
    throw "FAIL: $Name"
  }
  Write-Host "PASS: $Name"
}

Assert-Contains $schemaText '"allowed_sids"' "allowed_sids config exists"
Assert-Contains $mainText 'def _get_event_sid\(self, event' "sid extraction helper exists"
Assert-Contains $mainText 'for attr in \("unified_msg_origin", "sender_id", "user_id"\)' "sid extraction prefers UMO"
Assert-Contains $mainText 'def _is_allowed_event\(self, event' "event allowlist helper exists"
Assert-Contains $mainText 'uid = sid\.rsplit\(":", 1\)\[-1\]' "allowlist accepts numeric UID from UMO"
Assert-Contains $mainText 'def _blocked_result\(self, event' "blocked result helper exists"
Assert-NotContains $mainText 'get_sender_name' "sid allowlist does not trust sender display name"
Assert-NotContains $mainText '__blocked__' "safeword tool branch preserves cooldown message"
Assert-Contains $mainText 'if not self\._is_allowed_event\(event\):' "event handlers check allowlist"
Assert-Contains $mainText 'safe_state = dict\(plugin_ref\._state\)' "webui returns state snapshot"
Assert-Contains $mainText 'if path == "/state":\s+if not self\._check_auth\(pwd, token\):' "webui html loads before password auth"
Assert-Contains $mainText 'safeword_cd and time\.time\(\) < safeword_cd' "webui safeword guard exists"
Assert-Contains $mainText 'pink-remote' "pink remote body class is present"
Assert-Contains $mainText '--rose:' "pink theme CSS token exists"
Assert-Contains $mainText 'Sweet Remote' "pink remote subtitle is present"
Assert-Contains $mainText '@vibe\.command\("automsg"\)' "auto message diagnostic command exists"
Assert-Contains $mainText 'def _activate_auto_session\(self, event' "auto message session helper exists"
Assert-Contains $schemaText '"auto_message_session"' "auto message session config exists"
Assert-Contains $mainText 'def _configured_auto_message_session\(self' "configured auto session helper exists"
Assert-Contains $mainText 'plugin_ref\._restore_auto_session_from_config' "webui restores auto session from config"
Assert-Contains $mainText 'not self\._active_private_session[\s\S]*?self\._restore_auto_session_from_config' "sync loop restores missing auto session"
Assert-Contains $mainText '"expansion": \[' "low auto messages include expansion mode"
Assert-Contains $mainText '"cum": \[' "low auto messages include cum mode"
Assert-Contains $mainText 'auto_message_empty_candidates' "empty auto message candidates are logged"
Assert-Contains $schemaText '"auto_message_use_llm"' "auto message llm config exists"
Assert-Contains $schemaText '"auto_message_llm_policy"' "auto message llm policy config exists"
Assert-Contains $mainText 'def _should_use_auto_message_llm\(self, state_snapshot\)' "auto message llm policy helper exists"
Assert-Contains $mainText 'policy == "key_states"' "auto message llm key state policy exists"
Assert-Contains $mainText 'policy == "every_3"' "auto message llm every third policy exists"
Assert-Contains $mainText 'async def _build_auto_message_llm\(self, state_snapshot\)' "auto message llm helper exists"
Assert-Contains $mainText 'await self\._build_auto_message_for_send' "auto message generation happens before send"
Assert-Contains $mainText '_build_auto_message\(state_snapshot\)' "auto message keeps word bank fallback"
Assert-Contains $mainText 'def _reset_auto_message_markers\(self' "auto message marker reset helper exists"
Assert-Contains $mainText 'while True:\s+_auto_state_snapshot = None[\s\S]*?_safeword_sleep = False[\s\S]*?try:' "sync loop send guards initialized before try"
Assert-Contains $mainText 'STATE_VERSION = \d+' "state version constant exists"
Assert-Contains $mainText '"stateVersion": STATE_VERSION' "default state includes stateVersion"
Assert-Contains $mainText 'def _migrate_state\(self, data\)' "state migration helper exists"
Assert-Contains $mainText 'self\._state = self\._migrate_state\(self\._state\)' "initial state is migrated"
Assert-Contains $mainText 'data = self\._migrate_state\(data\)' "loaded state is migrated"
Assert-Contains $mainText 'import secrets' "webui token uses secrets module"
Assert-Contains $mainText 'WEBUI_TOKEN_TTL' "webui token ttl exists"
Assert-Contains $mainText 'def _issue_webui_token\(self\)' "webui token issue helper exists"
Assert-Contains $mainText 'def _validate_webui_token\(self, token\)' "webui token validate helper exists"
Assert-Contains $mainText 'path == "/auth"' "webui auth endpoint exists"
Assert-Contains $mainText '"token": plugin_ref\._issue_webui_token\(\)' "webui auth returns token"
Assert-Contains $mainText 'X-Vibe-Token' "webui accepts token header"
Assert-Contains $mainText 'AUTH_TOKEN' "webui frontend uses token"
Assert-Contains $mainText 'typeof pwdArg === ''string''' "webui login ignores click event object"
Assert-Contains $mainText 'addEventListener\(''click'',\(\)=>login\(\)\)' "webui login button does not pass click event as password"
Assert-Contains $mainText 'localStorage\.setItem\(''vibe_token''' "webui stores token instead of password"
Assert-NotContains $mainText 'localStorage\.setItem\(''vibe_pwd''' "webui no longer stores password"
Assert-Contains $mainText 'PLAY_TASKS = \[' "light play task pool exists"
Assert-Contains $mainText 'ACHIEVEMENTS = \{[\s\S]*?PLAY_TASKS = \[[\s\S]*?CLIMAX_FACE' "play task pool is python top-level before constants"
Assert-Contains $mainText '"playTask"' "play state field exists"
Assert-Contains $mainText '@vibe\.command\("play"\)' "play command exists"
Assert-Contains $mainText '@vibe\.command\("roll"\)' "roll command exists"
Assert-Contains $mainText '@filter\.command_group\("0721"\)' "short chinese 0721 command group exists"
Assert-Contains $mainText 'async def cmd_cn_task' "short task command exists"
Assert-Contains $mainText 'async def cmd_cn_done' "short done command exists"
Assert-Contains $mainText 'async def cmd_cn_skip' "short skip command exists"
Assert-Contains $mainText 'async def cmd_cn_roll' "short roll command exists"
Assert-Contains $mainText 'path == "/play"' "webui play action endpoint exists"
Assert-Contains $mainText 'play-btn' "webui play buttons exist"
Assert-Contains $mainText 'sendPlayAction\(''task''\)' "webui task button calls play endpoint"
Assert-Contains $mainText 'sendPlayAction\(''roll''\)' "webui roll button calls play endpoint"
Assert-Contains $mainText 'def _play_status_text\(self, s\)' "play status helper exists"
Assert-Contains $mainText 'action in \("task", "done", "roll"\)[\s\S]*?safeword_cd and time\.time\(\) < safeword_cd' "play task respects safeword cooldown"
Assert-Contains $mainText 'renderPlay\(\)' "webui renders play state"
Assert-Contains $mainText 'if _safeword_sleep:\s+await asyncio\.sleep\(1\)\s+continue' "safeword branch skips normal state machine"
Assert-Contains $mainText 'self\._update_diary\(now, dt, self\._state\["active"\]\)\s+\# 4\.[\s\S]*?self\._flush_to_file\(\)' "diary update happens before flush"

$lines = Get-Content -Encoding UTF8 $main
$lockIndent = $null
for ($i = 0; $i -lt $lines.Count; $i++) {
  $line = $lines[$i]
  $indent = ($line.Length - $line.TrimStart().Length)
  if ($null -ne $lockIndent -and $line.Trim().Length -gt 0 -and $indent -le $lockIndent) {
    $lockIndent = $null
  }
  if ($line -match 'with self\._state_lock:') {
    $lockIndent = $indent
    continue
  }
  if ($null -ne $lockIndent -and $line -match 'yield event\.plain_result') {
    throw "FAIL: yield inside state lock at line $($i + 1)"
  }
}
Write-Host "PASS: no yield inside state lock"

if (Test-Path $zip) {
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  $sourceVersion = [regex]::Match($metadataText, 'version:\s*([^\r\n]+)').Groups[1].Value.Trim()
  $archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
  try {
    $entries = @($archive.Entries | ForEach-Object { $_.FullName.Replace('\', '/') })
    foreach ($required in @(
      'astrbot_plugin_0721_mode/main.py',
      'astrbot_plugin_0721_mode/metadata.yaml',
      'astrbot_plugin_0721_mode/README.md',
      'astrbot_plugin_0721_mode/requirements.txt',
      'astrbot_plugin_0721_mode/_conf_schema.json'
    )) {
      if ($entries -notcontains $required) { throw "FAIL: zip missing $required" }
      Write-Host "PASS: zip contains $required"
    }
    if ($entries | Where-Object { $_ -match '__pycache__' }) { throw "FAIL: zip contains __pycache__" }
    Write-Host "PASS: zip has no __pycache__"

    function Read-ZipText($Archive, $Name) {
      $entry = $Archive.GetEntry($Name)
      if ($null -eq $entry) { $entry = $Archive.GetEntry($Name.Replace('/', '\')) }
      if ($null -eq $entry) { throw "FAIL: missing zip entry $Name" }
      $reader = New-Object System.IO.StreamReader($entry.Open())
      try { return $reader.ReadToEnd() } finally { $reader.Dispose() }
    }

    $zipMainText = Read-ZipText $archive 'astrbot_plugin_0721_mode/main.py'
    $zipMetadataText = Read-ZipText $archive 'astrbot_plugin_0721_mode/metadata.yaml'
    $zipSchemaText = Read-ZipText $archive 'astrbot_plugin_0721_mode/_conf_schema.json'
    $zipVersion = [regex]::Match($zipMetadataText, 'version:\s*([^\r\n]+)').Groups[1].Value.Trim()
    if ($zipVersion -ne $sourceVersion) { throw "FAIL: zip version $zipVersion != source version $sourceVersion" }
    Write-Host "PASS: zip version matches source"
    if ($zipMainText -ne $mainText) { throw "FAIL: zip main.py differs from source" }
    Write-Host "PASS: zip main.py matches source"
    if ($zipSchemaText -ne $schemaText) { throw "FAIL: zip _conf_schema.json differs from source" }
    Write-Host "PASS: zip _conf_schema.json matches source"
  } finally {
    $archive.Dispose()
  }
}

Write-Host "Static checks completed."
