<?php
/**
 * Endpoint JSON pour la command palette (⌘K).
 *
 * Renvoie un mix de technologies + offres matchant la requête.
 *
 * Exemple : GET /api/palette.php?q=python
 */

declare(strict_types=1);

['pdo' => $pdo] = require __DIR__ . '/../../src/bootstrap.php';

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: public, max-age=30');

$q = trim((string) ($_GET['q'] ?? ''));
if ($q === '' || mb_strlen($q) < 2) {
    echo json_encode(['technologies' => [], 'offers' => []]);
    exit;
}

$like = $q . '%';
$likeMid = '%' . $q . '%';

// ── Technologies ──
$techSql = 'SELECT t.canonical_name, t.display_name, t.category, '
    . 'COUNT(DISTINCT ot.offer_id) AS n '
    . 'FROM technologies t '
    . 'LEFT JOIN offer_technologies ot ON ot.technology_id = t.id '
    . 'LEFT JOIN offers o ON o.id = ot.offer_id AND o.is_active = 1 '
    . 'WHERE t.display_name LIKE :q1 '
    . 'OR t.canonical_name LIKE :q2 '
    . 'OR JSON_SEARCH(LOWER(t.aliases), \'one\', :q3) IS NOT NULL '
    . 'GROUP BY t.id '
    . 'HAVING n > 0 '
    . 'ORDER BY n DESC, LENGTH(t.display_name) '
    . 'LIMIT 5';
$stmt = $pdo->prepare($techSql);
$stmt->bindValue(':q1', $like);
$stmt->bindValue(':q2', $like);
$stmt->bindValue(':q3', '%' . strtolower($q) . '%');
$stmt->execute();
$technologies = array_map(
    static fn (array $r) => [
        'canonical_name' => (string) $r['canonical_name'],
        'display_name' => (string) $r['display_name'],
        'category' => (string) $r['category'],
        'n' => (int) $r['n'],
    ],
    $stmt->fetchAll(),
);

// ── Offres ──
$offerSql = 'SELECT o.id, o.title, o.city, c.name AS company_name '
    . 'FROM offers o '
    . 'INNER JOIN companies c ON c.id = o.company_id '
    . 'WHERE o.is_active = 1 '
    . 'AND (o.title LIKE :q_title OR c.name LIKE :q_company) '
    . 'ORDER BY o.posted_at DESC, o.id DESC '
    . 'LIMIT 7';
$stmt = $pdo->prepare($offerSql);
$stmt->bindValue(':q_title', $likeMid);
$stmt->bindValue(':q_company', $likeMid);
$stmt->execute();
$offers = array_map(
    static fn (array $r) => [
        'id' => (int) $r['id'],
        'title' => (string) $r['title'],
        'city' => $r['city'] ? (string) $r['city'] : null,
        'company_name' => $r['company_name'] ? (string) $r['company_name'] : null,
    ],
    $stmt->fetchAll(),
);

echo json_encode(['technologies' => $technologies, 'offers' => $offers], JSON_UNESCAPED_UNICODE);
