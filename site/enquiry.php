<?php
/**
 * Enquiry form handler for www.pathdriveway.co.zw (static site on cPanel).
 *
 * Emails a validated enquiry to the business inbox using the host's own mail server.
 * Nothing is stored except a short-lived, hashed per-visitor counter used to stop spam floods.
 * Works on PHP 7.2 and later.
 *
 * Replies: JSON for the site's JavaScript; a redirect or a small HTML page for browsers without JavaScript.
 */
declare(strict_types=1);

// ---- Settings ---------------------------------------------------------------------------------
const ENQUIRY_TO    = 'admin@pathdriveway.co.zw';
const ENQUIRY_FROM  = 'admin@pathdriveway.co.zw';  // an address on this domain, so the host's mail server will send it
const SITE_ORIGINS  = ['https://www.pathdriveway.co.zw', 'https://pathdriveway.co.zw'];
const PER_VISITOR   = 5;      // enquiries allowed per visitor...
const VISITOR_SPAN  = 900;    // ...every 15 minutes
const SITE_WIDE     = 40;     // enquiries allowed from everyone combined...
const SITE_SPAN     = 3600;   // ...every hour (caps a flood even if visitor IPs are faked)
const MAX_BYTES     = 20000;  // largest request accepted
const SERVICES = [
    'paving'       => 'Paving',
    'tarmac'       => 'Tarmac construction',
    'construction' => 'Building & renovations',
    'pavers'       => 'Pavers (supply only)',
    'other'        => 'Something else',
];
// ------------------------------------------------------------------------------------------------

ini_set('display_errors', '0');
date_default_timezone_set('Africa/Harare');
header('X-Content-Type-Options: nosniff');
header('Cache-Control: no-store');

$wantsJson = stripos((string) ($_SERVER['HTTP_ACCEPT'] ?? ''), 'application/json') !== false;

function respond(int $status, bool $ok, string $message, bool $json): void
{
    http_response_code($status);
    if ($json) {
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode(['ok' => $ok, 'message' => $message]);
    } elseif ($ok) {
        header('Location: /thank-you/', true, 303);
    } else {
        header('Content-Type: text/html; charset=utf-8');
        $m = htmlspecialchars($message, ENT_QUOTES, 'UTF-8');
        echo '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            . '<meta name="robots" content="noindex"><title>Enquiry not sent | Pathfinder Driveways</title>'
            . '<style>body{margin:0;font:1rem/1.6 system-ui,sans-serif;color:#2B2B2B;background:#F6F4EE}main{max-width:36rem;margin:4rem auto;padding:0 1rem}'
            . 'h1{color:#1B2340;font-size:1.75rem;line-height:1.2}a{color:#1B2340;font-weight:600}</style></head><body><main>'
            . '<h1>Your enquiry wasn&rsquo;t sent</h1><p>' . $m . '</p>'
            . '<p><a href="/contact/#enquiry">Go back to the form</a>, WhatsApp us on <a href="https://wa.me/263789734406">078&nbsp;973&nbsp;4406</a>, '
            . 'call <a href="tel:+263242788113">0242&nbsp;788&nbsp;113</a> or email <a href="mailto:' . ENQUIRY_TO . '">' . ENQUIRY_TO . '</a>.</p>'
            . '</main></body></html>';
    }
    exit;
}

/** Records one hit for $key and reports whether it was already over the limit. Fails open if storage is unavailable. */
function over_limit(string $key, int $limit, int $span): bool
{
    $dir = rtrim(sys_get_temp_dir(), '/\\') . DIRECTORY_SEPARATOR . 'pathfinder-enquiry';
    if (!is_dir($dir) && !@mkdir($dir, 0700, true) && !is_dir($dir)) {
        return false;
    }
    $stale = mt_rand(1, 50) === 1 ? glob($dir . DIRECTORY_SEPARATOR . '*.cnt') : false;  // tidy up now and then
    if (is_array($stale)) {
        foreach ($stale as $old) {
            if (is_file($old) && (int) filemtime($old) < time() - 86400) {
                @unlink($old);
            }
        }
    }
    // The visitor's IP is never written down: only a keyed hash of it.
    $file = $dir . DIRECTORY_SEPARATOR . hash_hmac('sha256', $key, __DIR__ . php_uname('n')) . '.cnt';
    $fh = @fopen($file, 'c+');
    if ($fh === false) {
        return false;
    }
    flock($fh, LOCK_EX);
    $now = time();
    $hits = array_filter(array_map('intval', explode(',', (string) stream_get_contents($fh))), function ($t) use ($now, $span) {
        return $t > $now - $span;
    });
    $over = count($hits) >= $limit;
    if (!$over) {
        $hits[] = $now;
    }
    ftruncate($fh, 0);
    rewind($fh);
    fwrite($fh, implode(',', $hits));
    flock($fh, LOCK_UN);
    fclose($fh);
    return $over;
}

/** A single-line text field: trimmed, control characters removed, rejected if too long or not valid UTF-8. */
function text_field(string $name, int $max, bool $multiline = false): ?string
{
    $v = $_POST[$name] ?? '';
    if (!is_string($v) || preg_match('//u', $v) !== 1) {
        return null;
    }
    $v = $multiline
        ? preg_replace('/[^\P{C}\n\t]+/u', '', str_replace("\r\n", "\n", $v))
        : preg_replace('/[\p{C}]+/u', ' ', $v);
    $v = trim((string) $v);
    $len = function_exists('mb_strlen') ? mb_strlen($v, 'UTF-8') : strlen($v);
    return $len > $max ? null : $v;
}

// ---- Request checks ----------------------------------------------------------------------------
if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    header('Allow: POST');
    respond(405, false, 'Please use the enquiry form on the Contact page.', $wantsJson);
}
if ((int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > MAX_BYTES) {
    respond(413, false, 'Your message is too long. Please shorten it and try again.', $wantsJson);
}
$origin = (string) ($_SERVER['HTTP_ORIGIN'] ?? '');
$self = ((!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http') . '://' . ($_SERVER['HTTP_HOST'] ?? '');
if ($origin !== '' && $origin !== $self && !in_array($origin, SITE_ORIGINS, true)) {
    respond(403, false, 'Please send your enquiry from the Pathfinder website.', $wantsJson);
}
// Hidden "company" field: people never see it, bots fill it in. Pretend success and send nothing.
if (trim((string) ($_POST['company'] ?? '')) !== '') {
    respond(200, true, 'Thank you. Your enquiry has been sent.', $wantsJson);
}
// Behind Cloudflare the visitor's address arrives in CF-Connecting-IP. It can be faked by bypassing
// Cloudflare, which is why there is also a site-wide cap.
$visitor = (string) ($_SERVER['HTTP_CF_CONNECTING_IP'] ?? ($_SERVER['REMOTE_ADDR'] ?? 'unknown'));
if (over_limit('site', SITE_WIDE, SITE_SPAN) || over_limit('ip:' . $visitor, PER_VISITOR, VISITOR_SPAN)) {
    respond(429, false, 'We have received several enquiries from this connection. Please wait a few minutes, or WhatsApp or call us instead.', $wantsJson);
}

// ---- Validation --------------------------------------------------------------------------------
$name     = text_field('name', 100);
$phone    = text_field('phone', 30);
$email    = text_field('email', 254);
$service  = text_field('service', 20);
$location = text_field('location', 120);
$message  = text_field('message', 3000, true);

$problems = [];
if ($name === null || $name === '') {
    $problems[] = 'your name';
}
if ($phone === null || !preg_match('/^[0-9+()\-. ]{7,30}$/', $phone) || strlen((string) preg_replace('/\D/', '', $phone)) < 7) {
    $problems[] = 'a phone number we can reach you on';
}
if ($email === null || ($email !== '' && filter_var($email, FILTER_VALIDATE_EMAIL) === false)) {
    $problems[] = 'a valid email address (or leave it blank)';
}
if ($service === null || !array_key_exists($service, SERVICES)) {
    $problems[] = 'the service you need';
}
if ($location === null) {
    $problems[] = 'a shorter project location';
}
if ($message === null || $message === '') {
    $problems[] = 'a short description of your project';
}
if ($problems) {
    respond(422, false, 'Please add ' . implode(', ', $problems) . '.', $wantsJson);
}

// ---- Send --------------------------------------------------------------------------------------
// Visitor text only ever goes into the message body, or into headers after validation and encoding,
// so nobody can add recipients or headers.
$subject = 'Website enquiry: ' . SERVICES[$service] . ' - ' . $name;
$body = "New enquiry from the Pathfinder website\n\n"
    . "Name: {$name}\n"
    . "Phone / WhatsApp: {$phone}\n"
    . 'Email: ' . ($email !== '' ? $email : '-') . "\n"
    . 'Service: ' . SERVICES[$service] . "\n"
    . 'Project location: ' . ($location !== '' ? $location : '-') . "\n\n"
    . "Brief description:\n{$message}\n\n"
    . '-- ' . "\nSent " . date('j F Y, H:i') . " (Harare time) from www.pathdriveway.co.zw\n";
$headers = [
    'From: =?UTF-8?B?' . base64_encode('Pathfinder website') . '?= <' . ENQUIRY_FROM . '>',
    'MIME-Version: 1.0',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: 8bit',
];
if ($email !== '') {
    $headers[] = 'Reply-To: ' . $email;
}

$dryRun = getenv('PATHFINDER_MAIL_DRYRUN');  // local testing only: write the email to this file instead of sending
if ($dryRun) {
    $sent = file_put_contents($dryRun, "To: " . ENQUIRY_TO . "\nSubject: =?UTF-8?B?" . base64_encode($subject) . "?=\n"
        . implode("\n", $headers) . "\n\n" . $body . "\n=====\n", FILE_APPEND | LOCK_EX) !== false;
} else {
    $sent = mail(ENQUIRY_TO, '=?UTF-8?B?' . base64_encode($subject) . '?=', $body, implode("\r\n", $headers), '-f' . ENQUIRY_FROM);
}

if (!$sent) {
    respond(500, false, 'Sorry, we couldn\'t send your enquiry just now.', $wantsJson);
}
respond(200, true, 'Thank you. Your enquiry has been sent. We\'ll be in touch soon.', $wantsJson);
