<?php
/**
 * Page d'accueil — hero + stats + top technos + dernières offres paginées (niveau 1).
 */

declare(strict_types=1);

use TechPulse\Repos\OfferRepository;

['pdo' => $pdo, 'twig' => $twig] = require __DIR__ . '/../src/bootstrap.php';

$repo = new OfferRepository($pdo);

$page = max(1, (int) ($_GET['page'] ?? 1));
$offers = $repo->listPaginated($page, 20);
$stats = $repo->globalStats();
$topTechs = $repo->topTechnologies(12);

echo $twig->render('index.twig', [
    'offers' => $offers,
    'page' => $page,
    'stats' => $stats,
    'top_techs' => $topTechs,
]);
