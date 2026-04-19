<?php
/**
 * Comparateur d'offres côté à côté.
 *   /compare.php?ids=1,2,3 (jusqu'à 4 IDs)
 */

declare(strict_types=1);

use TechPulse\Repos\OfferRepository;

['pdo' => $pdo, 'twig' => $twig] = require __DIR__ . '/../src/bootstrap.php';

$idsParam = trim((string) ($_GET['ids'] ?? ''));
$ids = array_slice(
    array_filter(
        array_map('intval', explode(',', $idsParam)),
        static fn (int $v) => $v > 0,
    ),
    0,
    4,
);

$repo = new OfferRepository($pdo);
$offers = [];
foreach ($ids as $id) {
    $offer = $repo->find($id);
    if ($offer !== null) {
        $offers[] = $offer;
    }
}

echo $twig->render('compare.twig', ['offers' => $offers]);
