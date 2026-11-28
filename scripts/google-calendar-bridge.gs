/**
 * Sage Studio 개인일정 캘린더 <-> Google Calendar 양방향 동기화 브릿지 (Google Apps Script)
 *
 * [배포 방법]
 * 1. https://script.google.com 접속 -> "새 프로젝트" (또는 기존 프로젝트)
 * 2. 기존 코드를 모두 지우고 이 파일의 코드를 붙여넣은 뒤 저장 (Ctrl+S)
 * 3. 우측 상단 "배포" -> "새 배포" (수정 시 "배포 관리 -> 연필 아이콘 -> 새 버전") -> 유형: "웹 앱"
 * 4. 다음 사용자 권한으로 실행: "나", 액세스 권한이 있는 사용자: "모든 사용자" 선택 후 "배포"
 * 5. 생성된 웹 앱 URL (https://script.google.com/macros/s/.../exec)을
 *    포털의 [개인일정 캘린더 -> 연동 설정]에 입력
 */

function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet(e) {
  try {
    var params = (e && e.parameter) ? e.parameter : {};
    var action = params.action || 'list';

    if (action === 'ping') {
      return jsonResponse({ ok: true, message: 'Sage Studio Google Calendar Bridge Active' });
    }

    if (action === 'list') {
      var now = new Date();
      var year = parseInt(params.year, 10) || parseInt(Utilities.formatDate(now, 'Asia/Seoul', 'yyyy'), 10);
      var month = parseInt(params.month, 10) || parseInt(Utilities.formatDate(now, 'Asia/Seoul', 'MM'), 10);
      var monthPrefix = year + '-' + ('0' + month).slice(-2);

      // Pad by +-1 day to avoid UTC/Script timezone boundary misses
      var startDate = new Date(year, month - 1, 0, 0, 0, 0);
      var endDate = new Date(year, month, 2, 23, 59, 59);

      var cals = CalendarApp.getAllOwnedCalendars();
      if (!cals || cals.length === 0) {
        cals = [CalendarApp.getDefaultCalendar()];
      }

      var seen = {};
      var items = [];
      for (var c = 0; c < cals.length; c++) {
        var events = cals[c].getEvents(startDate, endDate);
        for (var i = 0; i < events.length; i++) {
          var ev = events[i];
          var evId = ev.getId();
          if (seen[evId]) continue;
          seen[evId] = true;

          var st = ev.getStartTime();
          var isAllDay = ev.isAllDayEvent();
          var dateStr = Utilities.formatDate(st, 'Asia/Seoul', 'yyyy-MM-dd');
          if (dateStr.indexOf(monthPrefix) !== 0) continue;

          var timeStr = isAllDay ? '종일' : Utilities.formatDate(st, 'Asia/Seoul', 'HH:mm');
          items.push({
            id: evId,
            title: ev.getTitle() || '(제목 없음)',
            dateStr: dateStr,
            timeStr: timeStr,
            description: ev.getDescription() || ''
          });
        }
      }

      return jsonResponse({ ok: true, items: items });
    }

    return jsonResponse({ ok: false, error: 'Unknown action: ' + action });
  } catch (err) {
    return jsonResponse({ ok: false, error: String(err) });
  }
}

function doPost(e) {
  try {
    var raw = (e && e.postData && e.postData.contents) ? e.postData.contents : '{}';
    var body = JSON.parse(raw);
    var action = body.action || '';
    var cal = CalendarApp.getDefaultCalendar();

    if (action === 'create' || action === 'update') {
      var dateStr = body.dateStr;
      var timeStr = /^\d{2}:\d{2}$/.test(body.time || '') ? body.time : '09:00';
      var type = body.type || '개인일정';
      var memo = body.memo || '';
      var title = '[' + type + '] ' + memo;
      var desc = 'Sage Studio 개인일정 캘린더 (' + type + ')';

      var startDt = new Date(dateStr + 'T' + timeStr + ':00+09:00');
      var endDt = new Date(startDt.getTime() + 60 * 60 * 1000);

      if (action === 'update' && body.gcalId) {
        var existing = cal.getEventById(body.gcalId);
        if (existing) {
          existing.setTitle(title);
          existing.setTime(startDt, endDt);
          existing.setDescription(desc);
          return jsonResponse({ ok: true, id: existing.getId() });
        }
      }

      var created = cal.createEvent(title, startDt, endDt, { description: desc });
      return jsonResponse({ ok: true, id: created.getId() });
    }

    if (action === 'delete' && body.gcalId) {
      var ev = cal.getEventById(body.gcalId);
      if (ev) {
        ev.deleteEvent();
      }
      return jsonResponse({ ok: true });
    }

    return jsonResponse({ ok: false, error: 'Unknown action: ' + action });
  } catch (err) {
    return jsonResponse({ ok: false, error: String(err) });
  }
}
