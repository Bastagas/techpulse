<?php
/**
 * Simulateur salaire — formulaire qui décrit un profil, POST API /simulator/salary.
 *
 * Remplit les selects (villes, technos, contrats) depuis les repos pour coller au
 * domaine réel du modèle ML.
 */

declare(strict_types=1);

use TechPulse\Repos\OfferRepository;
use TechPulse\Repos\TechRepository;

['pdo' => $pdo, 'twig' => $twig] = require __DIR__ . '/../src/bootstrap.php';

$offerRepo = new OfferRepository($pdo);
$techRepo = new TechRepository($pdo);

echo $twig->render('simulator.twig', [
    'cities' => $offerRepo->listDistinctCities(3),
    'contracts' => $offerRepo->listDistinctContracts(),
    'top_techs' => $techRepo->listWithCounts(5),
]);
