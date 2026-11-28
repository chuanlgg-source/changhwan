/**
 * Sage Studio 개인일정 캘린더 <-> Google Calendar 양방향 동기화 브릿지 (Google Apps Script)
 *
 * [배포 방법]
 * 1. https://script.google.com 접속 -> "새 프로젝트" 클릭
 * 2. 기존 코드를 모두 지우고 이 파일의 코드를 붙여넣은 뒤 저장 (Ctrl+S)
 * 3. 우측 상단 "배포" -> "새 배포" -> 유형: "웹 앱" 선택
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
      var year = parseInt(params.year, 10) || now.getFullYear();
      var month = parseInt(params.month, 10) || (now.getMonth() + 1);

      var startDate = new Date(year, month - 1, 1, 0, 0, 0);
      var endDate = new Date(year, month, 0, 23, 59, 59);

      var cal = CalendarApp.getDefaultCalendar();
      var events = cal.getEvents(startDate, endDate);
      var items = events.map(function (ev) {
        var st = ev.getStartTime();
        var isAllDay = ev.isAllDayEvent();
        var yyyy = st.getFullYear();
        var mm = ('0' + (st.getMonth() + 1)).slice(-2);
        var dd = ('0' + st.getDate()).slice(-2);
        var hh = ('0' + st.getHours()).slice(-2);
        var mi = ('0' + st.getMinutes()).slice(-2);

        return {
          id: ev.getId(),
          title: ev.getTitle() || '(제목 없음)',
          dateStr: yyyy + '-' + mm + '-' + dd,
          timeStr: isAllDay ? '종일' : (hh + ':' + mi),
          description: ev.getDescription() || ''
        };
      });

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
      var dateStr = body.dateStr; // YYYY-MM-DD
      var timeStr = /^\d{2}:\d{2}$/.test(body.time || '') ? body.time : '09:00';
      var type = body.type || '개인일정';
      var memo = body.memo || '';
      var title = '[' + type + '] ' + memo;
      var desc = 'Sage Studio 개인일정 캘린더 (' + type + ')';

      var parts = dateStr.split('-');
      var tParts = timeStr.split(':');
      var startDt = new Date(
        parseInt(parts[0], 10),
        parseInt(parts[1], 10) - 1,
        parseInt(parts[2], 10),
        parseInt(tParts[0], 10),
        parseInt(tParts[1], 10),
        0
      );
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
