<?php
/**
 * Page de désabonnement d'une alerte email.
 *   /unsubscribe.php?token=xxxxxxxxxxxxxxxxxxxxxxxx
 */

declare(strict_types=1);

use TechPulse\Db\Connection;

['twig' => $twig] = require __DIR__ . '/../src/bootstrap.php';

$pdo = Connection::get();
$token = trim((string) ($_GET['token'] ?? ''));
$confirmed = isset($_GET['confirm']);
$result = null;
$alert = null;

if ($token === '') {
    $result = ['type' => 'error', 'msg' => 'Token manquant.'];
} else {
    $stmt = $pdo->prepare('SELECT * FROM alerts WHERE token = :t LIMIT 1');
    $stmt->execute([':t' => $token]);
    $alert = $stmt->fetch();

    if (!$alert) {
        $result = ['type' => 'error', 'msg' => 'Alerte introuvable ou déjà supprimée.'];
    } elseif ($confirmed) {
        $pdo->prepare('UPDATE alerts SET is_active = 0 WHERE token = :t')->execute([':t' => $token]);
        $result = ['type' => 'success', 'msg' => 'Ton alerte a bien été désactivée. Tu ne recevras plus d\'emails.'];
    }
}

echo $twig->render('unsubscribe.twig', [
    'token' => $token,
    'alert' => $alert,
    'result' => $result,
    'confirmed' => $confirmed,
]);
