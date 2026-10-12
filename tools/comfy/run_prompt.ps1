param(
    [Parameter(Mandatory = $true)]
    [string]$PromptPath,
    [string]$BaseUrl = 'http://127.0.0.1:8188',
    [int]$PollSeconds = 5
)

$ErrorActionPreference = 'Stop'
$resolvedPrompt = (Resolve-Path -LiteralPath $PromptPath).Path
$payload = Get-Content -Raw -LiteralPath $resolvedPrompt
$queued = Invoke-RestMethod -Uri "$BaseUrl/prompt" -Method Post -ContentType 'application/json' -Body $payload
$promptId = $queued.prompt_id

if (-not $promptId) {
    throw "ComfyUI did not return a prompt_id."
}

Write-Output "Queued prompt: $promptId"

while ($true) {
    Start-Sleep -Seconds $PollSeconds
    $history = Invoke-RestMethod -Uri "$BaseUrl/history/$promptId" -Method Get
    $item = $history.$promptId
    if ($null -eq $item) { continue }

    $status = $item.status.status_str
    Write-Output "Status: $status"
    if ($status -eq 'success') {
        foreach ($node in $item.outputs.PSObject.Properties.Value) {
            foreach ($image in @($node.images)) {
                if ($null -ne $image) {
                    Write-Output "$($image.type):$($image.subfolder)/$($image.filename)"
                }
            }
        }
        break
    }
    if ($status -eq 'error') {
        throw "ComfyUI render failed: $($item.status.messages | ConvertTo-Json -Depth 12)"
    }
}
