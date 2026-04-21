<?php
/**
 * Endpoint JSON pour le modal stats d'une techno (déclenché au clic sur tech-badge).
 *
 * Renvoie count total, salaire médian/p25/p75, top entreprises, top villes.
 *
 * Exemple : GET /api/tech_stats.php?name=python
 */

declare(strict_types=1);

['pdo' => $pdo] = require __DIR__ . '/../../src/bootstrap.php';

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: public, max-age=60');

$canonical = trim((string) ($_GET['name'] ?? ''));
if ($canonical === '') {
    http_response_code(400);
    echo json_encode(['error' => 'Missing name parameter']);
    exit;
}

// ── Tech row ──
$stmt = $pdo->prepare('SELECT id, canonical_name, display_name, category FROM technologies WHERE canonical_name = :n LIMIT 1');
$stmt->bindValue(':n', $canonical);
$stmt->execute();
$tech = $stmt->fetch();
if (!$tech) {
    http_response_code(404);
    echo json_encode(['error' => 'Unknown technology']);
    exit;
}
$techId = (int) $tech['id'];

// ── Global offer count + salary stats ──
$stmt = $pdo->prepare(
    'SELECT COUNT(DISTINCT o.id) AS total, '
    . 'COUNT(DISTINCT o.company_id) AS companies_count, '
    . 'COUNT(DISTINCT o.salary_min) AS with_salary '
    . 'FROM offers o '
    . 'INNER JOIN offer_technologies ot ON ot.offer_id = o.id '
    . 'WHERE ot.technology_id = :tid AND o.is_active = 1'
);
$stmt->bindValue(':tid', $techId, PDO::PARAM_INT);
$stmt->execute();
$agg = $stmt->fetch();

// Salaires pour percentiles (récupère tous et calcule en PHP, plus simple que window funcs)
$stmt = $pdo->prepare(
    'SELECT o.salary_min FROM offers o '
    . 'INNER JOIN offer_technologies ot ON ot.offer_id = o.id '
    . 'WHERE ot.technology_id = :tid AND o.is_active = 1 AND o.salary_min IS NOT NULL '
    . 'ORDER BY o.salary_min ASC'
);
$stmt->bindValue(':tid', $techId, PDO::PARAM_INT);
$stmt->execute();
$salaries = array_map('intval', array_column($stmt->fetchAll(), 'salary_min'));
$n = count($salaries);
$salary_median = $salary_p25 = $salary_p75 = null;
if ($n > 0) {
    $pct = static fn (float $p) => $salaries[min($n - 1, (int) floor($p * ($n - 1)))];
    $salary_median = $pct(0.5);
    $salary_p25 = $pct(0.25);
    $salary_p75 = $pct(0.75);
}

// ── Top companies ──
$stmt = $pdo->prepare(
    'SELECT c.name, COUNT(*) AS n FROM offers o '
    . 'INNER JOIN offer_technologies ot ON ot.offer_id = o.id '
    . 'INNER JOIN companies c ON c.id = o.company_id '
    . 'WHERE ot.technology_id = :tid AND o.is_active = 1 '
    . 'GROUP BY c.id ORDER BY n DESC, c.name LIMIT 6'
);
$stmt->bindValue(':tid', $techId, PDO::PARAM_INT);
$stmt->execute();
$top_companies = array_map(
    static fn (array $r) => ['name' => (string) $r['name'], 'n' => (int) $r['n']],
    $stmt->fetchAll()
);

// ── Top cities ──
$stmt = $pdo->prepare(
    'SELECT o.city, COUNT(*) AS n FROM offers o '
    . 'INNER JOIN offer_technologies ot ON ot.offer_id = o.id '
    . 'WHERE ot.technology_id = :tid AND o.is_active = 1 AND o.city IS NOT NULL '
    . 'GROUP BY o.city ORDER BY n DESC, o.city LIMIT 6'
);
$stmt->bindValue(':tid', $techId, PDO::PARAM_INT);
$stmt->execute();
$top_cities = array_map(
    static fn (array $r) => ['city' => (string) $r['city'], 'n' => (int) $r['n']],
    $stmt->fetchAll()
);

// Couleurs par catégorie (aligné avec tech_badge.twig)
$categoryColors = [
    'language'    => ['bg' => 'rgba(239, 68, 68, 0.15)',  'fg' => '#F87171'],
    'framework'   => ['bg' => 'rgba(168, 85, 247, 0.15)', 'fg' => '#C084FC'],
    'database'    => ['bg' => 'rgba(34, 211, 238, 0.15)', 'fg' => '#67E8F9'],
    'cloud'       => ['bg' => 'rgba(236, 72, 153, 0.15)', 'fg' => '#F9A8D4'],
    'tool'        => ['bg' => 'rgba(245, 158, 11, 0.15)', 'fg' => '#FCD34D'],
    'library'     => ['bg' => 'rgba(99, 102, 241, 0.15)', 'fg' => '#A5B4FC'],
    'methodology' => ['bg' => 'rgba(255, 255, 255, 0.06)','fg' => '#CBD5E1'],
];
$category = (string) $tech['category'];
$colors = $categoryColors[$category] ?? $categoryColors['methodology'];

echo json_encode([
    'canonical_name'   => (string) $tech['canonical_name'],
    'display_name'     => (string) $tech['display_name'],
    'category'         => $category,
    'color_bg'         => $colors['bg'],
    'color_fg'         => $colors['fg'],
    'total_offers'     => (int) $agg['total'],
    'companies_count'  => (int) $agg['companies_count'],
    'salary_median'    => $salary_median,
    'salary_p25'       => $salary_p25,
    'salary_p75'       => $salary_p75,
    'salary_count'     => $n,
    'top_companies'    => $top_companies,
    'top_cities'       => $top_cities,
], JSON_UNESCAPED_UNICODE);
