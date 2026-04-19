<?php
/**
 * Recherche avancée — mot-clé + ville + tech + contrat (niveau 2).
 */

declare(strict_types=1);

use TechPulse\Repos\OfferRepository;

['pdo' => $pdo, 'twig' => $twig] = require __DIR__ . '/../src/bootstrap.php';

$repo = new OfferRepository($pdo);

$filters = array_filter([
    'keyword' => trim((string) ($_GET['keyword'] ?? '')),
    'city' => trim((string) ($_GET['city'] ?? '')),
    'tech' => trim((string) ($_GET['tech'] ?? '')),
    'contract' => trim((string) ($_GET['contract'] ?? '')),
    'seniority' => trim((string) ($_GET['seniority'] ?? '')),
    'remote' => trim((string) ($_GET['remote'] ?? '')),
], static fn (string $v) => $v !== '');

$page = max(1, (int) ($_GET['page'] ?? 1));
$offers = $repo->listPaginated($page, 20, $filters);

$cities = $repo->listDistinctCities(3);
$contracts = $repo->listDistinctContracts();

echo $twig->render('search.twig', [
    'offers' => $offers,
    'page' => $page,
    'filters' => $filters,
    'cities' => $cities,
    'contracts' => $contracts,
]);
