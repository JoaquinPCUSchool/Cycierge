<?php
// Administrative reporting: weekly / monthly / yearly summaries of access + occupancy per unit.
// Used by admin/api/report.php (Android, session login) and admin/getreport.php (Pi dashboard, localhost only).
//
// Data sources
//   TBLLOGS    unlock events           -> tenant unlocks ("User1 Unlock Door") / admin unlocks ("Admin Unlock ...")
//   TBLRECORD  door detections         -> one row per IR-triggered recording (DT = YYYYMMDDHHMMSS)
//   TBLSTAYS   tenant check-in history -> NEW (written by user/updateuser.php), used for occupancy
//   TBLDAILY   per-day/per-room counts -> NEW (rolled up from TBLLOGS/TBLRECORD so that "Clear logs" /
//                                          "Delete data" no longer erase the reporting history)
require_once __DIR__ . '/lib.php';   // db(), arg()

const REPORT_TZ = 'Asia/Manila';

/** Machine endpoints (Pi dashboard): loopback only, and not via a reverse proxy (Tailscale Serve/Funnel adds X-Forwarded-For). */
function report_local_only(): void {
    $ip = $_SERVER['REMOTE_ADDR'] ?? '';
    if (!in_array($ip, ['127.0.0.1', '::1'], true) || isset($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        http_response_code(403);
        header('Content-Type: application/json');
        exit('{"error":"local only"}');
    }
}

/** 'YYYY-M-D' + 'H:MM[:SS]' (as typed on the Pi, not zero padded) -> 'YYYY-MM-DD HH:MM:SS', or null if it isn't a real date. */
function report_dt(string $d, string $t): ?string {
    if (!preg_match('/^(\d{4})-(\d{1,2})-(\d{1,2})/', trim($d), $m)) return null;
    if (!checkdate((int)$m[2], (int)$m[3], (int)$m[1])) return null;
    $h = $i = $s = 0;
    if (preg_match('/^(\d{1,2}):(\d{2})(?::(\d{2}))?/', trim($t), $x)) { $h = (int)$x[1]; $i = (int)$x[2]; $s = (int)($x[3] ?? 0); }
    if ($h > 23 || $i > 59 || $s > 59) { $h = $i = $s = 0; }
    return sprintf('%04d-%02d-%02d %02d:%02d:%02d', $m[1], $m[2], $m[3], $h, $i, $s);
}

/** Create the two report tables if missing, and seed TBLSTAYS from the tenants currently in TBLUSER. Idempotent. */
function report_prepare(mysqli $c): void {
    $c->query("CREATE TABLE IF NOT EXISTS TBLSTAYS (
        STAYID INT AUTO_INCREMENT PRIMARY KEY,
        ROOMID INT NOT NULL,
        TENANTNAME VARCHAR(100) NOT NULL DEFAULT '',
        TENANTID VARCHAR(60) NOT NULL DEFAULT '',
        CHECKIN DATETIME NOT NULL,
        CHECKOUT DATETIME NULL,
        KEY ix_room (ROOMID, CHECKIN)
    )");
    $c->query("CREATE TABLE IF NOT EXISTS TBLDAILY (
        D DATE NOT NULL,
        ROOMID INT NOT NULL,
        UNLOCKS_TENANT INT NOT NULL DEFAULT 0,
        UNLOCKS_ADMIN INT NOT NULL DEFAULT 0,
        DETECTIONS INT NOT NULL DEFAULT 0,
        PRIMARY KEY (D, ROOMID)
    )");

    // A room that has a tenant in TBLUSER but no stay yet gets one open stay (check-in = USERDATE/USERTIME).
    $has = $c->prepare("SELECT COUNT(*) FROM TBLSTAYS WHERE ROOMID = ?");
    $ins = $c->prepare("INSERT INTO TBLSTAYS (ROOMID, TENANTNAME, TENANTID, CHECKIN) VALUES (?, ?, ?, ?)");
    foreach ($c->query("SELECT ID, USERNAME, USERID, USERDATE, USERTIME FROM TBLUSER")->fetch_all(MYSQLI_ASSOC) as $r) {
        $room = (int)$r['ID'];
        $has->execute([$room]);
        if ((int)$has->get_result()->fetch_row()[0] > 0) continue;
        $ci = report_dt((string)$r['USERDATE'], (string)$r['USERTIME']);
        if ($ci === null || trim((string)$r['USERNAME']) === '') continue;
        $ins->execute([$room, (string)$r['USERNAME'], (string)$r['USERID'], $ci]);
    }
}

/** A new tenant was registered for $room: close the previous open stay and open a new one. */
function report_stay_open(mysqli $c, int $room, string $name, string $tid, string $date, string $time): void {
    $ci = report_dt($date, $time) ?? (new DateTimeImmutable('now', new DateTimeZone(REPORT_TZ)))->format('Y-m-d H:i:s');
    $c->prepare("UPDATE TBLSTAYS SET CHECKOUT = GREATEST(CHECKIN, ?) WHERE ROOMID = ? AND CHECKOUT IS NULL")->execute([$ci, $room]);
    $c->prepare("INSERT INTO TBLSTAYS (ROOMID, TENANTNAME, TENANTID, CHECKIN) VALUES (?, ?, ?, ?)")->execute([$room, $name, $tid, $ci]);
}

/** 'YYYY-M-D' or 'YYYYMMDD[...]' -> 'YYYY-MM-DD', or null if it isn't a real calendar date (never lets one bad row break a report). */
function report_norm_date(string $s): ?string {
    if (!preg_match('/^(\d{4})-(\d{1,2})-(\d{1,2})/', trim($s), $m) && !preg_match('/^(\d{4})(\d{2})(\d{2})/', trim($s), $m)) return null;
    return checkdate((int)$m[2], (int)$m[3], (int)$m[1]) ? sprintf('%04d-%02d-%02d', $m[1], $m[2], $m[3]) : null;
}

/**
 * Copy per-day counts from the raw tables into TBLDAILY. GREATEST() means a day's stored count never goes down,
 * so deleting raw rows (Clear logs / Delete data) keeps the history. Rows with an impossible date are skipped
 * (e.g. Pi-side unlocks logged by the old "%Y-%M-%d" bug). Dates are checked in PHP, not with STR_TO_DATE, because in
 * strict SQL mode one bad value would abort the whole query.
 * Any unlock whose text starts with "Admin" counts as admin; everything else counts as tenant.
 */
function report_rollup(mysqli $c): void {
    $acc = [];   // [room][date] = [tenant unlocks, admin unlocks, detections]
    $sql = "SELECT LOGSID AS room, LOGSDATE AS d, SUM(LOGSACTIVITY NOT LIKE 'Admin%') AS t, SUM(LOGSACTIVITY LIKE 'Admin%') AS a
            FROM TBLLOGS GROUP BY LOGSID, LOGSDATE";
    foreach ($c->query($sql)->fetch_all(MYSQLI_ASSOC) as $r) {
        $room = (int)$r['room']; $d = report_norm_date((string)$r['d']);
        if ($room < 1 || $d === null) continue;
        $acc[$room][$d][0] = ($acc[$room][$d][0] ?? 0) + (int)$r['t'];
        $acc[$room][$d][1] = ($acc[$room][$d][1] ?? 0) + (int)$r['a'];
    }
    $sql = "SELECT RECORDID AS room, LEFT(DT, 10) AS d, COUNT(*) AS n FROM TBLRECORD GROUP BY RECORDID, LEFT(DT, 10)";
    foreach ($c->query($sql)->fetch_all(MYSQLI_ASSOC) as $r) {
        $room = (int)$r['room']; $d = report_norm_date((string)$r['d']);
        if ($room < 1 || $d === null) continue;
        $acc[$room][$d][2] = ($acc[$room][$d][2] ?? 0) + (int)$r['n'];
    }
    $up = $c->prepare("INSERT INTO TBLDAILY (D, ROOMID, UNLOCKS_TENANT, UNLOCKS_ADMIN, DETECTIONS) VALUES (?, ?, ?, ?, ?)
        ON DUPLICATE KEY UPDATE UNLOCKS_TENANT = GREATEST(UNLOCKS_TENANT, VALUES(UNLOCKS_TENANT)),
                                UNLOCKS_ADMIN  = GREATEST(UNLOCKS_ADMIN,  VALUES(UNLOCKS_ADMIN)),
                                DETECTIONS     = GREATEST(DETECTIONS,     VALUES(DETECTIONS))");
    foreach ($acc as $room => $days) {
        foreach ($days as $d => $v) $up->execute([$d, $room, $v[0] ?? 0, $v[1] ?? 0, $v[2] ?? 0]);
    }
}

/** @return array{0:DateTimeImmutable,1:DateTimeImmutable} first and last day (inclusive) of the period containing $a */
function report_range(string $period, DateTimeImmutable $a): array {
    if ($period === 'year')  { $s = $a->setDate((int)$a->format('Y'), 1, 1);  return [$s, $s->setDate((int)$a->format('Y'), 12, 31)]; }
    if ($period === 'month') { $s = $a->modify('first day of this month');     return [$s, $a->modify('last day of this month')]; }
    $s = $a->modify('monday this week');                                      // week: Monday..Sunday
    return [$s, $s->modify('+6 days')];
}

/**
 * Build the report. Period is 'week' | 'month' | 'year'; $anchor is any 'Y-m-d' inside the wanted period (default: today).
 * Occupancy % = occupied days / days elapsed so far in the period (a still-running period is not penalised for future days).
 * A day is "occupied" if a stay covers any part of it.
 */
function report_summary(mysqli $c, string $period, ?string $anchor = null): array {
    $tz    = new DateTimeZone(REPORT_TZ);
    $today = new DateTimeImmutable('today', $tz);
    $a     = $anchor ? DateTimeImmutable::createFromFormat('!Y-m-d', $anchor, $tz) : false;
    if (!$a) $a = $today;
    if (!in_array($period, ['week', 'month', 'year'], true)) $period = 'week';

    [$start, $end] = report_range($period, $a);
    $last    = $end < $today ? $end : $today;                                  // last day that has happened
    $elapsed = $start > $today ? 0 : (int)$start->diff($last)->days + 1;
    $ymd     = fn(DateTimeImmutable $d) => $d->format('Y-m-d');

    // buckets: days for week/month, months for year
    $buckets = [];
    if ($period === 'year') {
        for ($m = 1; $m <= 12; $m++) {
            $f = $start->setDate((int)$start->format('Y'), $m, 1);
            $buckets[] = [$f->format('M'), $f, $f->modify('last day of this month')];
        }
    } else {
        for ($d = $start; $d <= $end; $d = $d->modify('+1 day')) $buckets[] = [$d->format('D j'), $d, $d];
    }

    // counts from TBLDAILY
    $daily = [];
    $q = $c->prepare("SELECT D, ROOMID, UNLOCKS_TENANT, UNLOCKS_ADMIN, DETECTIONS FROM TBLDAILY WHERE D BETWEEN ? AND ?");
    $q->execute([$ymd($start), $ymd($end)]);
    foreach ($q->get_result()->fetch_all(MYSQLI_ASSOC) as $r) {
        $daily[(int)$r['ROOMID']][$r['D']] = [(int)$r['UNLOCKS_TENANT'], (int)$r['UNLOCKS_ADMIN'], (int)$r['DETECTIONS']];
    }

    // occupied days + check-ins from TBLSTAYS
    $occ = []; $checkins = []; $names = [];
    $q = $c->prepare("SELECT ROOMID, TENANTNAME, CHECKIN, CHECKOUT FROM TBLSTAYS WHERE CHECKIN <= ? AND (CHECKOUT IS NULL OR CHECKOUT >= ?) ORDER BY CHECKIN");
    $q->execute([$ymd($end) . ' 23:59:59', $ymd($start) . ' 00:00:00']);
    foreach ($q->get_result()->fetch_all(MYSQLI_ASSOC) as $r) {
        $room = (int)$r['ROOMID'];
        if ($r['TENANTNAME'] !== '' && !in_array($r['TENANTNAME'], $names[$room] ?? [], true)) $names[$room][] = $r['TENANTNAME'];
        $s = new DateTimeImmutable(substr($r['CHECKIN'], 0, 10), $tz);
        $e = $r['CHECKOUT'] ? new DateTimeImmutable(substr($r['CHECKOUT'], 0, 10), $tz) : $today;
        if ($s >= $start && $s <= $end) $checkins[$room] = ($checkins[$room] ?? 0) + 1;
        for ($d = ($s > $start ? $s : $start), $stop = ($e < $last ? $e : $last); $d <= $stop; $d = $d->modify('+1 day')) {
            $occ[$room][$ymd($d)] = true;                                     // a set, so same-day hand-overs count once
        }
    }

    $rooms = [];
    $tot = ['unlocks_tenant' => 0, 'unlocks_admin' => 0, 'unlocks' => 0, 'detections' => 0, 'checkins' => 0, 'occupied_days' => 0];
    foreach ($c->query("SELECT ID FROM TBLUSER ORDER BY ID")->fetch_all(MYSQLI_ASSOC) as $u) {
        $room = (int)$u['ID'];
        $row = ['room' => $room, 'tenant' => implode(', ', $names[$room] ?? []), 'checkins' => $checkins[$room] ?? 0,
                'unlocks_tenant' => 0, 'unlocks_admin' => 0, 'unlocks' => 0, 'detections' => 0, 'occupied_days' => 0, 'buckets' => []];
        foreach ($buckets as [$label, $f, $t]) {
            $b = ['label' => $label, 'from' => $ymd($f), 'to' => $ymd($t), 'unlocks' => 0, 'detections' => 0, 'occupied_days' => 0];
            for ($d = $f; $d <= $t; $d = $d->modify('+1 day')) {
                $k = $ymd($d);
                [$ut, $ua, $det] = $daily[$room][$k] ?? [0, 0, 0];
                $row['unlocks_tenant'] += $ut; $row['unlocks_admin'] += $ua;
                $b['unlocks'] += $ut + $ua; $b['detections'] += $det;
                if (!empty($occ[$room][$k])) $b['occupied_days']++;
            }
            $row['detections']    += $b['detections'];
            $row['occupied_days'] += $b['occupied_days'];
            $row['buckets'][] = $b;
        }
        $row['unlocks']       = $row['unlocks_tenant'] + $row['unlocks_admin'];
        $row['occupancy_pct'] = $elapsed > 0 ? round(100 * $row['occupied_days'] / $elapsed, 1) : 0.0;
        foreach ($tot as $k => $_) $tot[$k] += $row[$k];
        $rooms[] = $row;
    }
    $tot['occupancy_pct'] = ($elapsed > 0 && $rooms) ? round(100 * $tot['occupied_days'] / ($elapsed * count($rooms)), 1) : 0.0;

    return ['period' => $period, 'start' => $ymd($start), 'end' => $ymd($end), 'days' => (int)$start->diff($end)->days + 1,
            'elapsed_days' => $elapsed, 'generated' => (new DateTimeImmutable('now', $tz))->format('Y-m-d H:i:s'),
            'rooms' => $rooms, 'totals' => $tot];
}
