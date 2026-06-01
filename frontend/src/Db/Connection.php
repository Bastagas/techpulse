<?php
/**
 * Singleton PDO — connexion MySQL pour le frontend TechPulse.
 */

declare(strict_types=1);

namespace TechPulse\Db;

use PDO;
use PDOException;
use RuntimeException;

final class Connection
{
    private static ?PDO $instance = null;

    public static function get(): PDO
    {
        if (self::$instance !== null) {
            return self::$instance;
        }

        $host = $_ENV['MYSQL_HOST'] ?? '127.0.0.1';
        $port = $_ENV['MYSQL_PORT'] ?? '3306';
        $db = $_ENV['MYSQL_DATABASE'] ?? 'techpulse';
        $user = $_ENV['MYSQL_USER'] ?? 'techpulse';
        $pass = $_ENV['MYSQL_PASSWORD'] ?? 'techpass';

        // Force TCP : PDO mappe `localhost` sur le socket Unix par défaut,
        // or MySQL tourne dans Docker et n'expose pas de socket sur le host.
        if ($host === 'localhost') {
            $host = '127.0.0.1';
        }

        $dsn = sprintf(
            'mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4',
            $host,
            $port,
            $db,
        );

        try {
            self::$instance = new PDO($dsn, $user, $pass, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ]);
        } catch (PDOException $e) {
            throw new RuntimeException(
                'Connexion BDD impossible. Vérifiez .env.local et que MySQL tourne. ' .
                    'Détail : ' . $e->getMessage(),
                (int) $e->getCode(),
                $e,
            );
        }

        return self::$instance;
    }
}
