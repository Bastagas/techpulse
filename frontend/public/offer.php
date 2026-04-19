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

// Récupère ML (salary + similarity) via l'API Flask
$apiPort = $_ENV['API_PORT'] ?? '5001';
$ctx = stream_context_create(['http' => ['timeout' => 2.0]]);

$salaryPrediction = null;
$apiResponse = @file_get_contents("http://127.0.0.1:{$apiPort}/offers/{$id}/salary-prediction", false, $ctx);
if ($apiResponse !== false) {
    $salaryPrediction = json_decode($apiResponse, true) ?: null;
}

$similar = [];
$simResponse = @file_get_contents("http://127.0.0.1:{$apiPort}/offers/{$id}/similar", false, $ctx);
if ($simResponse !== false) {
    $decoded = json_decode($simResponse, true);
    if ($decoded && !empty($decoded['items'])) {
        $similar = $decoded['items'];
    }
}

echo $twig->render('offer.twig', [
    'offer' => $offer,
    'salary_prediction' => $salaryPrediction,
    'similar_offers' => $similar,
]);
