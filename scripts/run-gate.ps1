# Local eval gate — run before push. No GitHub Actions required.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Suite = Join-Path $Root "examples\fire-inspection-extraction\suite.yaml"
$Good = Join-Path $Root "examples\fire-inspection-extraction\fixtures\good"
$Regressed = Join-Path $Root "examples\fire-inspection-extraction\fixtures\regressed"
$Baseline = Join-Path $Root "examples\fire-inspection-extraction\baseline.json"

Write-Host "==> Core tests (library only, no platform deps)"
python -m pytest -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "==> Good fixtures (must pass)"
python -m invarianteval.cli run $Suite `
  --provider fixture `
  --fixtures $Good `
  --baseline $Baseline `
  --fail-on-invariant
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "==> Regressed fixtures (must fail - proves gate catches auto-fill)"
python -m invarianteval.cli run $Suite `
  --provider fixture `
  --fixtures $Regressed `
  --fail-on-invariant `
  --format github-summary 2>$null
if ($LASTEXITCODE -eq 0) {
  Write-Error "Regressed fixtures should have failed"
  exit 1
}
Write-Host "OK: regressed fixtures correctly blocked"

Write-Host ""
Write-Host "Gate passed."
