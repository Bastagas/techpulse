<?php
/**
 * Export CSV / JSON des résultats d'une recherche.
 *
 * Utilise les mêmes filtres que search.php :
 *   /export.php?format=csv&tech=python&city=Nantes
 *   /export.php?format=json&keyword=data
 */

declare(strict_types=1);

use TechPulse\Repos\OfferRepository;

['pdo' => $pdo] = require __DIR__ . '/../src/bootstrap.php';

$format = ($_GET['format'] ?? 'csv') === 'json' ? 'json' : 'csv';
$limit = min(5000, max(10, (int) ($_GET['limit'] ?? 1000)));

$filters = array_filter([
    'keyword' => trim((string) ($_GET['keyword'] ?? '')),
    'city' => trim((string) ($_GET['city'] ?? '')),
    'tech' => trim((string) ($_GET['tech'] ?? '')),
    'contract' => trim((string) ($_GET['contract'] ?? '')),
], static fn (string $v) => $v !== '');

$repo = new OfferRepository($pdo);
$result = $repo->listPaginated(1, $limit, $filters);
$offers = $result['items'];

$filename = 'techpulse_offers_' . date('Ymd_His') . '.' . $format;

if ($format === 'json') {
    header('Content-Type: application/json; charset=utf-8');
    header('Content-Disposition: attachment; filename="' . $filename . '"');
    echo json_encode(
        ['exported_at' => date('c'), 'count' => count($offers), 'filters' => $filters, 'offers' => $offers],
        JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT,
    );
    exit;
}

// CSV
header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename="' . $filename . '"');

$out = fopen('php://output', 'w');
// BOM UTF-8 pour Excel
fwrite($out, "\xEF\xBB\xBF");
// 5e arg '' désactive le backslash-escape (RFC 4180 compliant) — requis PHP 8.4+
fputcsv(
    $out,
    ['id', 'title', 'company', 'sector', 'city', 'dept', 'contract', 'experience',
     'salary_min', 'salary_max', 'posted_at', 'source', 'url', 'technologies'],
    ',',
    '"',
    '',
);
foreach ($offers as $o) {
    fputcsv($out, [
        $o['id'],
        $o['title'],
        $o['company_name'],
        $o['company_sector'] ?? '',
        $o['city'] ?? '',
        $o['department_code'] ?? '',
        $o['contract_type'] ?? '',
        $o['experience_level'] ?? '',
        $o['salary_min'] ?? '',
        $o['salary_max'] ?? '',
        $o['posted_at'] ?? '',
        $o['source'],
        $o['source_url'] ?? '',
        implode(', ', array_column($o['technologies'] ?? [], 'display_name')),
    ], ',', '"', '');
}
fclose($out);
