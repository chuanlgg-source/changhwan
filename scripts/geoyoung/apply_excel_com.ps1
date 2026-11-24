param(
    [Parameter(Mandatory = $true)]
    [string]$PlanPath
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Release-Com($obj) {
    if ($null -ne $obj) {
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($obj) } catch {}
    }
}

$planRaw = Get-Content -Path $PlanPath -Raw -Encoding UTF8
$plan = $planRaw | ConvertFrom-Json

$excel = $null
$wb = $null
$wsDetail = $null
$wsSummary = $null

try {
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.ScreenUpdating = $false
    $excel.EnableEvents = $false

    $targetPath = [System.IO.Path]::GetFullPath($plan.targetPath)
    $wb = $excel.Workbooks.Open($targetPath)
    # xlCalculationManual = -4135 (대용량 COUNTIF 수식 재계산 방지로 속도 대폭 향상)
    $excel.Calculation = -4135
    $wsDetail = $wb.Worksheets.Item($plan.detailSheet)

    # 필터가 걸려 숨겨진 행이 있으면 해제
    $hadAutoFilter = $wsDetail.AutoFilterMode
    if ($wsDetail.FilterMode) {
        try { $wsDetail.ShowAllData() } catch {}
    }

    $amtCol = [int]$plan.amountCol
    $dueCol = [int]$plan.dueDateCol
    $billStart = [int]$plan.billStartRow
    $billSubRow = [int]$plan.billSubtotalRow
    $cashStart = [int]$plan.cashStartRow
    $cashSubRow = [int]$plan.cashSubtotalRow
    $totalRow = [int]$plan.totalRow

    # 1. 기존 어음/현금 섹션 당월 예정금액(G열)을 0으로 초기화, 어음 만기일(I열) 초기화
    if ($billSubRow -gt $billStart) {
        $billCount = $billSubRow - $billStart
        $zerosBill = New-Object 'object[,]' $billCount, 1
        $emptyDates = New-Object 'object[,]' $billCount, 1
        for ($i = 0; $i -lt $billCount; $i++) {
            $zerosBill[$i, 0] = 0
            $emptyDates[$i, 0] = $null
        }
        $rngBillAmt = $wsDetail.Range($wsDetail.Cells.Item($billStart, $amtCol), $wsDetail.Cells.Item($billSubRow - 1, $amtCol))
        $rngBillAmt.Value2 = $zerosBill
        Release-Com $rngBillAmt

        if ($plan.updateDueDate -and $dueCol -gt 0) {
            $rngBillDue = $wsDetail.Range($wsDetail.Cells.Item($billStart, $dueCol), $wsDetail.Cells.Item($billSubRow - 1, $dueCol))
            $rngBillDue.Value2 = $emptyDates
            Release-Com $rngBillDue
        }
    }

    if ($cashSubRow -gt $cashStart) {
        $cashCount = $cashSubRow - $cashStart
        $zerosCash = New-Object 'object[,]' $cashCount, 1
        for ($i = 0; $i -lt $cashCount; $i++) {
            $zerosCash[$i, 0] = 0
        }
        $rngCashAmt = $wsDetail.Range($wsDetail.Cells.Item($cashStart, $amtCol), $wsDetail.Cells.Item($cashSubRow - 1, $amtCol))
        $rngCashAmt.Value2 = $zerosCash
        Release-Com $rngCashAmt
    }

    # 2. 기존 매칭 행에 금액 및 만기일 반영
    foreach ($u in $plan.updates) {
        $r = [int]$u.row
        $wsDetail.Cells.Item($r, $amtCol).Value2 = [double]$u.amount
        if ($plan.updateDueDate -and $dueCol -gt 0 -and $u.dueDate) {
            $dt = [DateTime]::ParseExact($u.dueDate, "yyyy-MM-dd", $null)
            $wsDetail.Cells.Item($r, $dueCol).Value2 = $dt.ToOADate()
        }
    }

    # 헬퍼: 소계 행 바로 위에 새 행 삽입 (깨끗한 일반 중간 행을 템플릿으로 사용)
    function Insert-RowsBeforeSubtotal($ws, $sectionStartRow, $subtotalRow, $items, $kindLabel) {
        $insertedCount = 0
        $currSubRow = $subtotalRow
        # 소계 바로 위 마지막 행은 하단 테두리가 다를 수 있으므로 일반 중간 데이터 행을 템플릿으로 사용
        $templateRow = [Math]::Min($sectionStartRow + 5, $currSubRow - 2)
        if ($templateRow -lt $sectionStartRow) { $templateRow = $sectionStartRow }

        foreach ($item in $items) {
            $dstRow = $ws.Rows.Item($currSubRow)
            # xlDown = -4121, xlFormatFromLeftOrAbove = 0
            $dstRow.Insert(-4121, 0) | Out-Null
            Release-Com $dstRow

            $newRow = $currSubRow
            # 템플릿 행의 서식(테두리, 폰트, 숫자/날짜형식, 정렬 등) 정확히 복사
            $srcFmt = $ws.Range($ws.Cells.Item($templateRow, 1), $ws.Cells.Item($templateRow, 16))
            $dstFmt = $ws.Range($ws.Cells.Item($newRow, 1), $ws.Cells.Item($newRow, 16))
            $srcFmt.Copy() | Out-Null
            # xlPasteFormats = -4122
            $dstFmt.PasteSpecial(-4122) | Out-Null
            $ws.Rows.Item($newRow).RowHeight = $ws.Rows.Item($templateRow).RowHeight
            Release-Com $srcFmt
            Release-Com $dstFmt

            $ws.Cells.Item($newRow, 2).Value2 = [string]$item.buyerCode
            $ws.Cells.Item($newRow, 3).Value2 = [string]$item.buyerName
            $ws.Cells.Item($newRow, 4).Value2 = [string]$item.customerCode
            $ws.Cells.Item($newRow, 5).Value2 = [string]$item.customerName
            $ws.Cells.Item($newRow, 6).Value2 = 0
            $ws.Cells.Item($newRow, $amtCol).Value2 = [double]$item.amount
            $ws.Cells.Item($newRow, 8).Value2 = $kindLabel
            if ($plan.updateDueDate -and $dueCol -gt 0) {
                if ($item.dueDate) {
                    $dt = [DateTime]::ParseExact($item.dueDate, "yyyy-MM-dd", $null)
                    $ws.Cells.Item($newRow, $dueCol).Value2 = $dt.ToOADate()
                } else {
                    $ws.Cells.Item($newRow, $dueCol).Value2 = $null
                }
            }
            $ws.Cells.Item($newRow, 11).Value2 = $null
            $ws.Cells.Item($newRow, 12).Value2 = 0
            $ws.Cells.Item($newRow, 13).Value2 = $null

            $currSubRow++
            $insertedCount++
        }
        return $insertedCount
    }

    # 3. 아래쪽(현금 소계 위) 먼저 삽입 -> 위쪽(어음 소계 위) 나중 삽입하여 행 번호 꼬임 방지
    $cashInserted = 0
    if ($plan.insertCash -and $plan.insertCash.Count -gt 0) {
        $cashInserted = Insert-RowsBeforeSubtotal $wsDetail $cashStart $cashSubRow $plan.insertCash "현금"
    }

    $billInserted = 0
    if ($plan.insertBill -and $plan.insertBill.Count -gt 0) {
        $billInserted = Insert-RowsBeforeSubtotal $wsDetail $billStart $billSubRow $plan.insertBill "어음"
    }

    # 4. 최종 소계/합계 행 위치 산정
    $finalBillSubRow = $billSubRow + $billInserted
    $finalCashStart = $cashStart + $billInserted
    $finalCashSubRow = $cashSubRow + $billInserted + $cashInserted
    $finalTotalRow = $totalRow + $billInserted + $cashInserted

    # 5. 섹션별 정렬 (유형[어음 -> 현금] > 매입처명(C열) > 거래처명(E열)) 및 서식/수식 완벽 통일
    function Sort-And-FormatSection($ws, $startRow, $endRow, $kindLabel) {
        if ($endRow -lt $startRow) { return }

        # 정렬 전 깨끗한 중간 행의 서식을 기준 행으로 확보 (startRow + 5)
        $refRow = [Math]::Min($startRow + 5, $endRow)
        $refHeight = $ws.Rows.Item($refRow).RowHeight

        # 정렬: 매입처명(C열) 오름차순 -> 거래처명(E열) 오름차순
        if ($endRow -gt $startRow) {
            $sortRng = $ws.Range($ws.Cells.Item($startRow, 1), $ws.Cells.Item($endRow, 24))
            $key1 = $ws.Range($ws.Cells.Item($startRow, 3), $ws.Cells.Item($endRow, 3))
            $key2 = $ws.Range($ws.Cells.Item($startRow, 5), $ws.Cells.Item($endRow, 5))

            $ws.Sort.SortFields.Clear()
            # xlSortOnValues = 0, xlAscending = 1, xlSortNormal = 0
            [void]$ws.Sort.SortFields.Add($key1, 0, 1, 0)
            [void]$ws.Sort.SortFields.Add($key2, 0, 1, 0)
            $ws.Sort.SetRange($sortRng)
            $ws.Sort.Header = 2      # xlNo
            $ws.Sort.MatchCase = $false
            $ws.Sort.Orientation = 1 # xlTopToBottom
            $ws.Sort.Apply()

            Release-Com $key1
            Release-Com $key2
            Release-Com $sortRng
        }

        # 정렬 후 수식 일괄 재적용 (상대참조 정확 보장)
        $ws.Range("A${startRow}:A${endRow}").Formula = "=C${startRow}&D${startRow}&""${kindLabel}"""
        $ws.Range("J${startRow}:J${endRow}").Formula = "=+G${startRow}-F${startRow}"
        $ws.Range("N${startRow}:N${endRow}").Formula = "=IF(F${startRow}+G${startRow}<>0,""유"",""무"")"
        $ws.Range("O${startRow}:O${endRow}").Formula = "=IF(COUNTIF(A:A,A${startRow})>1,""중복"","""")"

        # 섹션 전체 서식 통일 (폰트, 테두리, 숫자/날짜 서식, 정렬, 행높이 누락 0%)
        $fmtSrc = $ws.Range($ws.Cells.Item($refRow, 1), $ws.Cells.Item($refRow, 16))
        $fmtDst = $ws.Range($ws.Cells.Item($startRow, 1), $ws.Cells.Item($endRow, 16))
        $fmtSrc.Copy() | Out-Null
        $fmtDst.PasteSpecial(-4122) | Out-Null
        $ws.Range("A${startRow}:A${endRow}").EntireRow.RowHeight = $refHeight

        # 모든 데이터 셀(B~M열)의 테두리를 thin으로 깔끔하게 보장 (누락된 가로/세로선 보완)
        $gridRng = $ws.Range($ws.Cells.Item($startRow, 2), $ws.Cells.Item($endRow, 13))
        # xlEdgeLeft=7, xlEdgeTop=8, xlEdgeBottom=9, xlEdgeRight=10, xlInsideVertical=11, xlInsideHorizontal=12
        # xlContinuous=1, xlThin=2
        foreach ($edge in @(7, 8, 9, 10, 11, 12)) {
            $b = $gridRng.Borders.Item($edge)
            $b.LineStyle = 1
            $b.Weight = 2
            $b.ColorIndex = -4105 # xlAutomatic
            Release-Com $b
        }
        Release-Com $gridRng
        Release-Com $fmtSrc
        Release-Com $fmtDst
    }

    Sort-And-FormatSection $wsDetail $billStart ($finalBillSubRow - 1) "어음"
    Sort-And-FormatSection $wsDetail $finalCashStart ($finalCashSubRow - 1) "현금"

    # 소계 행 상단 테두리(medium = -4138) 복원 보장
    foreach ($subR in @($finalBillSubRow, $finalCashSubRow)) {
        $subRng = $wsDetail.Range($wsDetail.Cells.Item($subR, 2), $wsDetail.Cells.Item($subR, 13))
        $topB = $subRng.Borders.Item(8)
        $topB.LineStyle = 1
        $topB.Weight = -4138
        Release-Com $topB
        Release-Com $subRng
    }

    # 6. 소계/합계 행 SUM 수식 범위 보정
    foreach ($colIdx in @(6, $amtCol, 10, 12)) {
        $colLetter = [char](64 + $colIdx)
        $wsDetail.Cells.Item($finalBillSubRow, $colIdx).Formula = "=SUM(${colLetter}${billStart}:${colLetter}$($finalBillSubRow - 1))"
        $wsDetail.Cells.Item($finalCashSubRow, $colIdx).Formula = "=SUM(${colLetter}${finalCashStart}:${colLetter}$($finalCashSubRow - 1))"
        $wsDetail.Cells.Item($finalTotalRow, $colIdx).Formula = "=${colLetter}${finalBillSubRow}+${colLetter}${finalCashSubRow}"
    }

    # AutoFilter 범위를 새로 확장된 전체 데이터 범위로 갱신
    if ($hadAutoFilter) {
        try {
            $wsDetail.AutoFilterMode = $false
            $afRng = $wsDetail.Range("A3:X${finalTotalRow}")
            [void]$afRng.AutoFilter()
            Release-Com $afRng
        } catch {}
    }

    # xlCalculationAutomatic = -4105 복원 후 1회 전체 재계산
    $excel.Calculation = -4105
    $excel.CalculateFull()

    $detailBillSum = [double]$wsDetail.Cells.Item($finalBillSubRow, $amtCol).Value2
    $detailCashSum = [double]$wsDetail.Cells.Item($finalCashSubRow, $amtCol).Value2
    $detailTotalSum = [double]$wsDetail.Cells.Item($finalTotalRow, $amtCol).Value2

    # 7. 집계 시트 소계 갱신 (옵션 활성 시)
    $summaryBillSum = $null
    $summaryCashSum = $null
    $summaryTotalSum = $null
    if ($plan.updateSummarySheet -and $plan.summarySheet) {
        try {
            $wsSummary = $wb.Worksheets.Item($plan.summarySheet)
            $sBillRow = [int]$plan.summaryBillRow
            $sCashRow = [int]$plan.summaryCashRow
            $sTotalRow = [int]$plan.summaryTotalRow
            $sAmtCol = [int]$plan.summaryAmountCol
            if ($sBillRow -gt 0 -and $sCashRow -gt 0 -and $sAmtCol -gt 0) {
                $wsSummary.Cells.Item($sBillRow, $sAmtCol).Value2 = $detailBillSum
                $wsSummary.Cells.Item($sCashRow, $sAmtCol).Value2 = $detailCashSum
                $excel.CalculateFull()
                $summaryBillSum = [double]$wsSummary.Cells.Item($sBillRow, $sAmtCol).Value2
                $summaryCashSum = [double]$wsSummary.Cells.Item($sCashRow, $sAmtCol).Value2
                if ($sTotalRow -gt 0) {
                    $summaryTotalSum = [double]$wsSummary.Cells.Item($sTotalRow, $sAmtCol).Value2
                }
            }
        } catch {
            # 집계 시트 갱신 실패 시에도 내역 시트 결과는 보존
        }
    }

    $wb.Save()

    $result = @{
        ok = $true
        targetPath = $targetPath
        billInserted = $billInserted
        cashInserted = $cashInserted
        finalBillSubtotalRow = $finalBillSubRow
        finalCashSubtotalRow = $finalCashSubRow
        finalTotalRow = $finalTotalRow
        detailBillSum = $detailBillSum
        detailCashSum = $detailCashSum
        detailTotalSum = $detailTotalSum
        summaryBillSum = $summaryBillSum
        summaryCashSum = $summaryCashSum
        summaryTotalSum = $summaryTotalSum
    }
    $result | ConvertTo-Json -Depth 4 -Compress
}
catch {
    $errObj = @{
        ok = $false
        error = $_.Exception.Message
    }
    $errObj | ConvertTo-Json -Depth 3 -Compress
    exit 1
}
finally {
    if ($null -ne $wb) {
        try { $wb.Close($false) } catch {}
    }
    if ($null -ne $excel) {
        try { $excel.Quit() } catch {}
    }
    Release-Com $wsSummary
    Release-Com $wsDetail
    Release-Com $wb
    Release-Com $excel
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
