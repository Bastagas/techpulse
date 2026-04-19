<?php
/**
 * Page "À propos" — narratif du projet + stats live.
 */

declare(strict_types=1);

use TechPulse\Repos\OfferRepository;

['pdo' => $pdo, 'twig' => $twig] = require __DIR__ . '/../src/bootstrap.php';

$repo = new OfferRepository($pdo);
$stats = $repo->globalStats();

echo $twig->render('about.twig', ['stats' => $stats]);
