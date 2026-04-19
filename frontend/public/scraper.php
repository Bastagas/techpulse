<?php
/**
 * Page "Scraper Status" — supervision du pipeline (live).
 *
 * Affiche :
 *  - Les derniers runs (scrape_runs) : date, spider, status, offres trouvées/nouvelles/maj
 *  - Des KPI d'activité des 30 derniers jours
 *  - Un mini-graph de la croissance de la BDD
 *  - L'état du scheduler (APScheduler cron daily 03:00 UTC)
 */

declare(strict_types=1);

['pdo' => $pdo, 'twig' => $twig] = require __DIR__ . '/../src/bootstrap.php';

// ── Runs récents ──
$runs = $pdo->query(
    'SELECT id, spider, started_at, finished_at, status, '
    . 'offers_found, offers_new, offers_updated, errors_count, '
    . 'TIMESTAMPDIFF(SECOND, started_at, finished_at) AS duration_s '
    . 'FROM scrape_runs ORDER BY id DESC LIMIT 20'
)->fetchAll();

// ── Agrégats 30 jours ──
$aggregates = $pdo->query(
    'SELECT COUNT(*) AS runs_total, '
    . 'SUM(offers_new) AS offers_new_30d, '
    . 'SUM(offers_updated) AS offers_updated_30d, '
    . 'SUM(errors_count) AS errors_30d, '
    . 'AVG(TIMESTAMPDIFF(SECOND, started_at, finished_at)) AS avg_duration, '
    . 'SUM(CASE WHEN status = "success" THEN 1 ELSE 0 END) AS success_count, '
    . 'SUM(CASE WHEN status = "failed" THEN 1 ELSE 0 END) AS failed_count '
    . 'FROM scrape_runs '
    . 'WHERE started_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)'
)->fetch();

// ── Cumul d'offres par jour (timeline) ──
$timeline = $pdo->query(
    'SELECT DATE(started_at) AS d, SUM(offers_new) AS n '
    . 'FROM scrape_runs '
    . 'WHERE started_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) AND status = "success" '
    . 'GROUP BY DATE(started_at) ORDER BY d ASC'
)->fetchAll();

// ── KPI BDD instantanée ──
$snapshot = $pdo->query(
    'SELECT COUNT(*) AS total, '
    . 'SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active, '
    . 'COUNT(DISTINCT company_id) AS companies, '
    . 'COUNT(DISTINCT city) AS cities, '
    . 'MAX(scraped_at) AS last_scraped '
    . 'FROM offers'
)->fetch();

// ── État scheduler (best-effort : appel API) ──
$scheduler = ['status' => 'unknown', 'next_run' => null];
$apiPort = $_ENV['API_PORT'] ?? '5001';
$ctx = stream_context_create(['http' => ['timeout' => 1.5]]);
$healthResp = @file_get_contents("http://127.0.0.1:{$apiPort}/health", false, $ctx);
if ($healthResp !== false) {
    $scheduler['status'] = 'running';
    $scheduler['next_run'] = '03:00 UTC (daily)';
}

echo $twig->render('scraper.twig', [
    'runs' => $runs,
    'aggregates' => $aggregates,
    'timeline' => $timeline,
    'snapshot' => $snapshot,
    'scheduler' => $scheduler,
]);
