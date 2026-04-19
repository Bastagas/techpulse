<?php
/**
 * Fiche détail d'une offre.
 */

declare(strict_types=1);

use TechPulse\Repos\OfferRepository;

['pdo' => $pdo, 'twig' => $twig] = require __DIR__ . '/../src/bootstrap.php';

$id = (int) ($_GET['id'] ?? 0);
if ($id <= 0) {
    http_response_code(404);
    echo 'Offre introuvable.';
    exit;
}

$repo = new OfferRepository($pdo);
$offer = $repo->find($id);

if ($offer === null) {
    http_response_code(404);
    echo $twig->render('layout.twig', []);
    exit;
}

echo $twig->render('offer.twig', ['offer' => $offer]);
