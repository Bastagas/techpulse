<?php
declare(strict_types=1);

namespace TechPulse\Tests;

use PDO;
use PHPUnit\Framework\TestCase;
use TechPulse\Repos\OfferRepository;

/**
 * Tests d'intégration PHPUnit sur OfferRepository.
 *
 * Prérequis : MySQL local (Docker ou MAMP) peuplé.
 * Les tests valident la construction des requêtes + contrats de retour,
 * pas les données exactes (qui évoluent avec les scrapes).
 */
final class OfferRepositoryTest extends TestCase
{
    private static ?PDO $pdo = null;

    public static function setUpBeforeClass(): void
    {
        $host = getenv('MYSQL_HOST') ?: '127.0.0.1';
        $port = getenv('MYSQL_PORT') ?: '3306';
        $db   = getenv('MYSQL_DATABASE') ?: 'techpulse';
        $user = getenv('MYSQL_USER') ?: 'techpulse';
        $pass = getenv('MYSQL_PASSWORD') ?: 'techpass';
        $dsn = "mysql:host=$host;port=$port;dbname=$db;charset=utf8mb4";
        self::$pdo = new PDO($dsn, $user, $pass, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_EMULATE_PREPARES => false,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
    }

    public function test_global_stats_returns_valid_shape(): void
    {
        $repo = new OfferRepository(self::$pdo);
        $s = $repo->globalStats();
        $this->assertArrayHasKey('total', $s);
        $this->assertArrayHasKey('with_salary', $s);
        $this->assertArrayHasKey('companies', $s);
        $this->assertArrayHasKey('cities', $s);
        $this->assertIsInt($s['total']);
        $this->assertGreaterThanOrEqual(0, $s['total']);
    }

    public function test_list_paginated_respects_per_page(): void
    {
        $repo = new OfferRepository(self::$pdo);
        $result = $repo->listPaginated(1, 5);
        $this->assertArrayHasKey('items', $result);
        $this->assertArrayHasKey('total', $result);
        $this->assertArrayHasKey('pages', $result);
        $this->assertLessThanOrEqual(5, count($result['items']));
    }

    public function test_list_paginated_keyword_filter_matches_in_title_or_description(): void
    {
        // Regression test: le filtre keyword utilise 2 placeholders distincts
        // (:kw_title / :kw_desc) pour éviter SQLSTATE[HY093] en native prepares.
        $repo = new OfferRepository(self::$pdo);
        $result = $repo->listPaginated(1, 3, ['keyword' => 'python']);
        $this->assertArrayHasKey('items', $result);
        // Ne doit pas lever de PDOException
        $this->assertIsInt($result['total']);
    }

    public function test_list_paginated_contract_filter_applies(): void
    {
        $repo = new OfferRepository(self::$pdo);
        $result = $repo->listPaginated(1, 3, ['contract' => 'CDI']);
        $this->assertIsInt($result['total']);
        foreach ($result['items'] as $item) {
            $this->assertSame('CDI', $item['contract_type']);
        }
    }

    public function test_list_distinct_cities_returns_non_empty_for_populated_db(): void
    {
        $repo = new OfferRepository(self::$pdo);
        $cities = $repo->listDistinctCities(1);
        $this->assertIsArray($cities);
        // Si la BDD est peuplée, on attend au moins quelques villes
        $globalStats = $repo->globalStats();
        if ($globalStats['total'] > 100) {
            $this->assertNotEmpty($cities);
            $this->assertContainsOnly('string', $cities);
        }
    }

    public function test_top_technologies_returns_sorted_descending(): void
    {
        $repo = new OfferRepository(self::$pdo);
        $techs = $repo->topTechnologies(10);
        $this->assertIsArray($techs);
        $previousCount = PHP_INT_MAX;
        foreach ($techs as $t) {
            $this->assertArrayHasKey('name', $t);
            $this->assertArrayHasKey('count', $t);
            $this->assertArrayHasKey('category', $t);
            $this->assertLessThanOrEqual($previousCount, $t['count']);
            $previousCount = $t['count'];
        }
    }

    public function test_timeline_returns_chronological_order(): void
    {
        $repo = new OfferRepository(self::$pdo);
        $timeline = $repo->timeline(90);
        $this->assertIsArray($timeline);
        $previousDate = '0000-00-00';
        foreach ($timeline as $point) {
            $this->assertArrayHasKey('date', $point);
            $this->assertArrayHasKey('count', $point);
            $this->assertGreaterThanOrEqual($previousDate, $point['date']);
            $previousDate = $point['date'];
        }
    }
}
