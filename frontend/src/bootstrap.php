<?php
/**
 * Bootstrap commun : autoload, .env, PDO, Twig.
 *
 * Retourne un tableau avec les services partagés [pdo, twig].
 * Utilisé par tous les points d'entrée dans `public/`.
 */

declare(strict_types=1);

use Dotenv\Dotenv;
use TechPulse\Db\Connection;
use Twig\Environment;
use Twig\Loader\FilesystemLoader;
use Twig\TwigFilter;

require __DIR__ . '/../vendor/autoload.php';

// ─── Charge .env.local depuis la racine du projet ───
$projectRoot = dirname(__DIR__, 2);
if (file_exists($projectRoot . '/.env.local')) {
    Dotenv::createImmutable($projectRoot, '.env.local')->safeLoad();
} elseif (file_exists($projectRoot . '/.env')) {
    Dotenv::createImmutable($projectRoot, '.env')->safeLoad();
}

// ─── PDO ──────────────────────────────────────
$pdo = Connection::get();

// ─── Twig ─────────────────────────────────────
$twig = new Environment(
    new FilesystemLoader(__DIR__ . '/views'),
    [
        'cache' => false,
        'debug' => ($_ENV['APP_ENV'] ?? 'development') === 'development',
        'autoescape' => 'html',
    ],
);

// Filtre : formatte un salaire annuel (45000 → "45 000 €")
$twig->addFilter(new TwigFilter('salary', static function (?int $n): string {
    if ($n === null) {
        return '—';
    }
    return number_format($n, 0, ',', ' ') . ' €';
}));

// Filtre : raccourcit un texte
$twig->addFilter(new TwigFilter('excerpt', static function (?string $s, int $length = 200): string {
    if ($s === null || $s === '') {
        return '';
    }
    $s = strip_tags($s);
    if (mb_strlen($s) <= $length) {
        return $s;
    }
    return mb_substr($s, 0, $length) . '…';
}));

// Filtre : relative time (il y a 3 jours)
$twig->addFilter(new TwigFilter('ago', static function (?string $datetime): string {
    if ($datetime === null) {
        return '';
    }
    $ts = strtotime($datetime);
    if ($ts === false) {
        return '';
    }
    $diff = time() - $ts;
    if ($diff < 60) {
        return 'à l\'instant';
    }
    if ($diff < 3600) {
        return 'il y a ' . (int)($diff / 60) . ' min';
    }
    if ($diff < 86400) {
        return 'il y a ' . (int)($diff / 3600) . ' h';
    }
    if ($diff < 86400 * 30) {
        return 'il y a ' . (int)($diff / 86400) . ' j';
    }
    return date('d/m/Y', $ts);
}));

return [
    'pdo' => $pdo,
    'twig' => $twig,
];
