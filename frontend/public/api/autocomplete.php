<?php
/**
 * Endpoint JSON pour autocomplete sur les technos (consommé par Alpine.js côté front).
 *
 * Exemple : GET /api/autocomplete.php?q=pyth&limit=8
 */

declare(strict_types=1);

use TechPulse\Repos\TechRepository;

['pdo' => $pdo] = require __DIR__ . '/../../src/bootstrap.php';

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: public, max-age=60');

$query = trim((string) ($_GET['q'] ?? ''));
$limit = min(25, max(1, (int) ($_GET['limit'] ?? 8)));

$repo = new TechRepository($pdo);
echo json_encode($repo->search($query, $limit), JSON_UNESCAPED_UNICODE);
