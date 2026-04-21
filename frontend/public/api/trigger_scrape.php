<?php
/**
 * Proxy POST → Flask API /scraping/trigger.
 *
 * Permet au frontend JS d'appeler l'API sans souci CORS / URL absolue
 * (le frontend PHP et l'API Flask tournent dans deux containers Docker
 * différents, le client navigateur voit juste /api/trigger_scrape.php).
 */

declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'message' => 'Method not allowed — utilise POST']);
    exit;
}

$apiHost = $_ENV['API_HOST'] ?? 'api';
$apiPort = $_ENV['API_PORT'] ?? '5001';

$ch = curl_init("http://{$apiHost}:{$apiPort}/scraping/trigger");
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => '{}',
    CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 5,
]);

$body = curl_exec($ch);
$code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$err = curl_error($ch);
curl_close($ch);

if ($body === false) {
    http_response_code(502);
    echo json_encode(['ok' => false, 'message' => "API Flask injoignable : {$err}"]);
    exit;
}

http_response_code($code ?: 200);
echo $body;
