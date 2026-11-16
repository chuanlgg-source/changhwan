<#
회사 POP3(SSL) 메일 3개월 수신함 추출 스크립트 (Windows PowerShell 기본 내장 기능 사용)
- 서버: mail.geo-young.com
- 포트: 995 (POP3 over SSL)
- 계정: chuanl@geo-young.com

사용 방법 (PowerShell):
  .\pop3_company_sync.ps1
#>

$Pop3Host = "mail.geo-young.com"
$Pop3Port = 995
$Pop3User = "chuanl@geo-young.com"
$Days = 90
$OutputFile = "company_emails_3m.json"

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13

function Decode-MimeHeader([string]$raw) {
    if ([string]::IsNullOrWhiteSpace($raw)) { return "" }
    $unfolded = $raw -replace "\r?\n[ \t]+", " "
    $regex = [regex]'=\?([^?]+)\?([BQbq])\?([^?]*)\?='
    $decoded = $regex.Replace($unfolded, {
        param($m)
        $charset = $m.Groups[1].Value.ToLower()
        $encType = $m.Groups[2].Value.ToUpper()
        $data = $m.Groups[3].Value
        if ($charset -in @("ks_c_5601-1987", "euc-kr", "euc_kr")) { $charset = "cp949" }
        try {
            $enc = [System.Text.Encoding]::GetEncoding($charset)
        } catch {
            $enc = [System.Text.Encoding]::UTF8
        }
        if ($encType -eq "B") {
            $bytes = [Convert]::FromBase64String($data)
            return $enc.GetString($bytes)
        } else {
            $data = $data -replace "_", " "
            $ms = New-Object System.IO.MemoryStream
            for ($i = 0; $i -lt $data.Length; $i++) {
                if ($data[$i] -eq '=' -and $i + 2 -lt $data.Length) {
                    $hex = $data.Substring($i + 1, 2)
                    try {
                        $ms.WriteByte([Convert]::ToByte($hex, 16))
                        $i += 2
                        continue
                    } catch {}
                }
                $b = [System.Text.Encoding]::ASCII.GetBytes($data[$i].ToString())
                $ms.Write($b, 0, $b.Length)
            }
            return $enc.GetString($ms.ToArray())
        }
    })
    return $decoded.Trim()
}

function Read-Pop3Line($reader) {
    return $reader.ReadLine()
}

function Read-Pop3Multiline($reader) {
    $sb = New-Object System.Text.StringBuilder
    while ($true) {
        $line = $reader.ReadLine()
        if ($null -eq $line -or $line -eq ".") { break }
        if ($line.StartsWith("..")) { $line = $line.Substring(1) }
        [void]$sb.AppendLine($line)
    }
    return $sb.ToString()
}

function Send-Pop3Command($writer, $reader, [string]$cmd) {
    $writer.WriteLine($cmd)
    $writer.Flush()
    $resp = Read-Pop3Line $reader
    if (-not $resp -or -not $resp.StartsWith("+OK")) {
        throw "POP3 오류 ($cmd): $resp"
    }
    return $resp
}

function Parse-MailDate([string]$rawDate) {
    if ([string]::IsNullOrWhiteSpace($rawDate)) { return $null }
    $clean = ($rawDate -replace "\([^)]*\)", "").Trim()
    try {
        return [DateTimeOffset]::Parse($clean)
    } catch {
        return $null
    }
}

Write-Host "POP3 SSL 연결 대상: $Pop3Host`:$Pop3Port ($Pop3User)" -ForegroundColor Cyan
$secPass = Read-Host "이메일 비밀번호 입력 (화면에 표시되지 않음)" -AsSecureString
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secPass)
$password = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

if ([string]::IsNullOrEmpty($password)) {
    Write-Host "비밀번호가 입력되지 않아 종료합니다." -ForegroundColor Red
    exit 1
}

$tcp = New-Object System.Net.Sockets.TcpClient
$tcp.ReceiveTimeout = 30000
$tcp.SendTimeout = 30000
$tcp.Connect($Pop3Host, $Pop3Port)

$ssl = New-Object System.Net.Security.SslStream($tcp.GetStream(), $false)
$ssl.AuthenticateAsClient($Pop3Host)

$reader = New-Object System.IO.StreamReader($ssl, [System.Text.Encoding]::GetEncoding("ISO-8859-1"))
$writer = New-Object System.IO.StreamWriter($ssl, [System.Text.Encoding]::ASCII)

try {
    $banner = Read-Pop3Line $reader
    if (-not $banner.StartsWith("+OK")) { throw "서버 배너 오류: $banner" }

    [void](Send-Pop3Command $writer $reader "USER $Pop3User")
    [void](Send-Pop3Command $writer $reader "PASS $password")

    $stat = Send-Pop3Command $writer $reader "STAT"
    $parts = $stat.Split(" ")
    $count = [int]$parts[1]
    Write-Host "접속 성공! 전체 메일 수: $count 건" -ForegroundColor Green

    $cutoff = (Get-Date).AddDays(-$Days)
    $results = New-Object System.Collections.Generic.List[object]
    $consecutiveOld = 0

    for ($idx = $count; $idx -ge 1; $idx--) {
        [void](Send-Pop3Command $writer $reader "TOP $idx 0")
        $hdrText = Read-Pop3Multiline $reader

        $dateMatch = [regex]::Match($hdrText, "(?im)^Date:\s*(.+(?:\r?\n[ \t].+)*)")
        $dt = if ($dateMatch.Success) { Parse-MailDate $dateMatch.Groups[1].Value } else { $null }

        if ($null -ne $dt -and $dt.LocalDateTime -lt $cutoff) {
            $consecutiveOld++
            if ($consecutiveOld -ge 20) { break }
            continue
        }
        $consecutiveOld = 0

        [void](Send-Pop3Command $writer $reader "RETR $idx")
        $rawMail = Read-Pop3Multiline $reader

        $splitIdx = $rawMail.IndexOf("`r`n`r`n")
        if ($splitIdx -lt 0) { $splitIdx = $rawMail.IndexOf("`n`n") }
        $headersPart = if ($splitIdx -ge 0) { $rawMail.Substring(0, $splitIdx) } else { $rawMail }
        $bodyPart = if ($splitIdx -ge 0) { $rawMail.Substring($splitIdx).Trim() } else { "" }

        $subjMatch = [regex]::Match($headersPart, "(?im)^Subject:\s*(.+(?:\r?\n[ \t].+)*)")
        $fromMatch = [regex]::Match($headersPart, "(?im)^From:\s*(.+(?:\r?\n[ \t].+)*)")
        $idMatch = [regex]::Match($headersPart, "(?im)^Message-ID:\s*(.+)")

        $subject = if ($subjMatch.Success) { Decode-MimeHeader $subjMatch.Groups[1].Value } else { "(제목 없음)" }
        if ([string]::IsNullOrWhiteSpace($subject)) { $subject = "(제목 없음)" }
        $sender = if ($fromMatch.Success) { Decode-MimeHeader $fromMatch.Groups[1].Value } else { "알 수 없음" }
        $msgId = if ($idMatch.Success) { $idMatch.Groups[1].Value.Trim("<> `r`n") } else { "pop3_$idx" }
        $dateStr = if ($null -ne $dt) { $dt.LocalDateTime.ToString("yyyy-MM-dd HH:mm") } else { (Get-Date).ToString("yyyy-MM-dd HH:mm") }

        $snippet = ($bodyPart -replace "(?is)<(script|style).*?>.*?</\1>", " " -replace "<[^>]+>", " " -replace "\s+", " ").Trim()
        if ($snippet.Length -gt 350) { $snippet = $snippet.Substring(0, 350) }

        $results.Add([PSCustomObject]@{
            id = $msgId
            date = $dateStr
            sender = $sender
            subject = $subject
            snippet = $snippet
            status = "미처리"
            labels = "POP3, GEO-YOUNG"
        })

        if ($results.Count % 20 -eq 0) {
            Write-Host "추출 중... $($results.Count)건 수집됨" -ForegroundColor DarkGray
        }
    }

    $json = $results | ConvertTo-Json -Depth 4
    [System.IO.File]::WriteAllText((Join-Path (Get-Location) $OutputFile), $json, [System.Text.UTF8Encoding]::new($false))
    Write-Host "완료! 최근 $Days 일 메일 $($results.Count)건을 '$OutputFile'에 저장했습니다." -ForegroundColor Green
}
finally {
    try {
        $writer.WriteLine("QUIT")
        $writer.Flush()
    } catch {}
    $ssl.Close()
    $tcp.Close()
}
