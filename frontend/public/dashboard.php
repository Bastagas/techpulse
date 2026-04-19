<?php
/**
 * Dashboard analytique — Chart.js + Leaflet.
 *
 * Agrège tous les indicateurs en une page : stats, top techs, salaires,
 * distribution contrats, timeline et heatmap géographique.
 */

declare(strict_types=1);

use TechPulse\Repos\OfferRepository;

['pdo' => $pdo, 'twig' => $twig] = require __DIR__ . '/../src/bootstrap.php';

$repo = new OfferRepository($pdo);

echo $twig->render('dashboard.twig', [
    'stats' => $repo->globalStats(),
    'top_techs' => $repo->topTechnologies(20),
    'cities' => $repo->topCities(15),
    'contracts' => $repo->contractDistribution(),
    'salary_stats' => $repo->salaryStats(),
    'timeline' => $repo->timeline(30),
    'geo' => $repo->geoPoints(),
]);
