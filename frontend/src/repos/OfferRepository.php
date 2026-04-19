<?php
/**
 * Repository pour la table `offers` (+ jointures company et technologies).
 */

declare(strict_types=1);

namespace TechPulse\Repos;

use PDO;

final class OfferRepository
{
    public function __construct(private PDO $pdo)
    {
    }

    /**
     * Liste paginée avec filtres optionnels.
     *
     * @param array{
     *     keyword?: string,
     *     city?: string,
     *     tech?: string,
     *     contract?: string
     * } $filters
     *
     * @return array{items: list<array<string,mixed>>, total: int, pages: int}
     */
    public function listPaginated(int $page = 1, int $perPage = 20, array $filters = []): array
    {
        $page = max(1, $page);
        $perPage = min(max(1, $perPage), 100);
        $offset = ($page - 1) * $perPage;

        [$where, $params, $joinTech] = $this->buildWhere($filters);

        $countSql = 'SELECT COUNT(DISTINCT o.id) FROM offers o '
            . 'INNER JOIN companies c ON c.id = o.company_id '
            . ($joinTech ? 'INNER JOIN offer_technologies ot ON ot.offer_id = o.id '
                . 'INNER JOIN technologies t ON t.id = ot.technology_id ' : '')
            . $where;
        $stmt = $this->pdo->prepare($countSql);
        $stmt->execute($params);
        $total = (int) $stmt->fetchColumn();

        $sql = 'SELECT DISTINCT o.id, o.title, o.description, o.contract_type, '
            . 'o.experience_level, o.salary_min, o.salary_max, o.city, '
            . 'o.department_code, o.posted_at, o.source, o.source_url, '
            . 'c.name AS company_name, c.sector AS company_sector '
            . 'FROM offers o '
            . 'INNER JOIN companies c ON c.id = o.company_id '
            . ($joinTech ? 'INNER JOIN offer_technologies ot ON ot.offer_id = o.id '
                . 'INNER JOIN technologies t ON t.id = ot.technology_id ' : '')
            . $where
            . ' ORDER BY o.posted_at DESC, o.id DESC '
            . 'LIMIT :perPage OFFSET :offset';

        $stmt = $this->pdo->prepare($sql);
        foreach ($params as $k => $v) {
            $stmt->bindValue($k, $v);
        }
        $stmt->bindValue(':perPage', $perPage, PDO::PARAM_INT);
        $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
        $stmt->execute();
        $items = $stmt->fetchAll();

        // Enrichit chaque offre avec ses technos
        if ($items !== []) {
            $ids = array_map(static fn ($r) => (int) $r['id'], $items);
            $techsByOffer = $this->fetchTechsByOffers($ids);
            foreach ($items as &$item) {
                $item['technologies'] = $techsByOffer[(int) $item['id']] ?? [];
            }
        }

        $pages = $total > 0 ? (int) ceil($total / $perPage) : 1;

        return ['items' => $items, 'total' => $total, 'pages' => $pages];
    }

    /** @return array<string,mixed>|null */
    public function find(int $id): ?array
    {
        $sql = 'SELECT o.*, c.name AS company_name, c.sector AS company_sector, '
            . 'c.website AS company_website, c.logo_url AS company_logo '
            . 'FROM offers o '
            . 'INNER JOIN companies c ON c.id = o.company_id '
            . 'WHERE o.id = :id';
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute([':id' => $id]);
        $row = $stmt->fetch();
        if (!$row) {
            return null;
        }
        $techs = $this->fetchTechsByOffers([(int) $row['id']]);
        $row['technologies'] = $techs[(int) $row['id']] ?? [];
        return $row;
    }

    /**
     * Récupère les technos associées à une liste d'offres (1 seul SELECT).
     *
     * @param list<int> $offerIds
     * @return array<int, list<array{canonical_name:string,display_name:string,category:string}>>
     */
    private function fetchTechsByOffers(array $offerIds): array
    {
        if ($offerIds === []) {
            return [];
        }
        $placeholders = implode(',', array_fill(0, count($offerIds), '?'));
        $sql = 'SELECT ot.offer_id, t.canonical_name, t.display_name, t.category '
            . 'FROM offer_technologies ot '
            . 'INNER JOIN technologies t ON t.id = ot.technology_id '
            . 'WHERE ot.offer_id IN (' . $placeholders . ') '
            . 'ORDER BY ot.confidence_score DESC, t.display_name';
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute($offerIds);
        $result = [];
        foreach ($stmt->fetchAll() as $row) {
            $id = (int) $row['offer_id'];
            $result[$id][] = [
                'canonical_name' => $row['canonical_name'],
                'display_name' => $row['display_name'],
                'category' => $row['category'],
            ];
        }
        return $result;
    }

    /**
     * Construit la clause WHERE + params à partir des filtres.
     *
     * @param array<string, string> $filters
     * @return array{0: string, 1: array<string, string>, 2: bool}
     */
    private function buildWhere(array $filters): array
    {
        $conditions = ['o.is_active = 1'];
        $params = [];
        $joinTech = false;

        if (!empty($filters['keyword'])) {
            $conditions[] = '(o.title LIKE :kw OR o.description LIKE :kw)';
            $params[':kw'] = '%' . $filters['keyword'] . '%';
        }
        if (!empty($filters['city'])) {
            $conditions[] = 'o.city = :city';
            $params[':city'] = $filters['city'];
        }
        if (!empty($filters['tech'])) {
            $conditions[] = 't.canonical_name = :tech';
            $params[':tech'] = $filters['tech'];
            $joinTech = true;
        }
        if (!empty($filters['contract'])) {
            $conditions[] = 'o.contract_type = :contract';
            $params[':contract'] = $filters['contract'];
        }
        if (!empty($filters['seniority'])) {
            $conditions[] = 'o.seniority = :seniority';
            $params[':seniority'] = $filters['seniority'];
        }
        if (!empty($filters['remote'])) {
            $conditions[] = 'o.remote_policy = :remote';
            $params[':remote'] = $filters['remote'];
        }

        return [' WHERE ' . implode(' AND ', $conditions), $params, $joinTech];
    }

    /** @return list<string> */
    public function listDistinctCities(int $minOffers = 3): array
    {
        $sql = 'SELECT city FROM offers WHERE city IS NOT NULL AND is_active = 1 '
            . 'GROUP BY city HAVING COUNT(*) >= :n ORDER BY COUNT(*) DESC, city LIMIT 200';
        $stmt = $this->pdo->prepare($sql);
        $stmt->bindValue(':n', $minOffers, PDO::PARAM_INT);
        $stmt->execute();
        return array_column($stmt->fetchAll(), 'city');
    }

    /** @return list<string> */
    public function listDistinctContracts(): array
    {
        $sql = 'SELECT DISTINCT contract_type FROM offers '
            . 'WHERE contract_type IS NOT NULL AND is_active = 1 ORDER BY contract_type';
        return array_column($this->pdo->query($sql)->fetchAll(), 'contract_type');
    }

    /** @return array<string, int> */
    public function seniorityDistribution(): array
    {
        $rows = $this->pdo->query(
            'SELECT seniority, COUNT(*) n FROM offers '
                . 'WHERE seniority IS NOT NULL AND is_active = 1 '
                . 'GROUP BY seniority ORDER BY FIELD(seniority, "junior", "mid", "senior", "lead")'
        )->fetchAll();
        $result = [];
        foreach ($rows as $r) {
            $result[(string) $r['seniority']] = (int) $r['n'];
        }
        return $result;
    }

    /** @return array<string, int> */
    public function remoteDistribution(): array
    {
        $rows = $this->pdo->query(
            'SELECT remote_policy, COUNT(*) n FROM offers '
                . 'WHERE remote_policy IS NOT NULL AND is_active = 1 '
                . 'GROUP BY remote_policy ORDER BY n DESC'
        )->fetchAll();
        return array_combine(
            array_column($rows, 'remote_policy'),
            array_map('intval', array_column($rows, 'n')),
        );
    }

    /** @return array<string, int|float|string> */
    public function globalStats(): array
    {
        $row = $this->pdo->query(
            'SELECT COUNT(*) total, '
                . 'SUM(salary_min IS NOT NULL) with_salary, '
                . 'COUNT(DISTINCT company_id) companies, '
                . 'COUNT(DISTINCT city) cities '
                . 'FROM offers WHERE is_active = 1'
        )->fetch();
        $last = $this->pdo->query(
            'SELECT MAX(scraped_at) AS last FROM offers'
        )->fetch();
        return [
            'total' => (int) $row['total'],
            'with_salary' => (int) $row['with_salary'],
            'companies' => (int) $row['companies'],
            'cities' => (int) $row['cities'],
            'last_scraped' => $last['last'] ?? null,
        ];
    }

    /**
     * Top N villes par nombre d'offres.
     *
     * @return list<array{city:string, department_code:?string, count:int}>
     */
    public function topCities(int $n = 15): array
    {
        $sql = 'SELECT city, department_code, COUNT(*) count '
            . 'FROM offers WHERE city IS NOT NULL AND is_active = 1 '
            . 'GROUP BY city, department_code ORDER BY count DESC LIMIT :n';
        $stmt = $this->pdo->prepare($sql);
        $stmt->bindValue(':n', $n, PDO::PARAM_INT);
        $stmt->execute();
        return array_map(
            static fn (array $r) => [
                'city' => (string) $r['city'],
                'department_code' => $r['department_code'] ? (string) $r['department_code'] : null,
                'count' => (int) $r['count'],
            ],
            $stmt->fetchAll(),
        );
    }

    /**
     * Distribution des types de contrats.
     *
     * @return list<array{contract_type:string, count:int}>
     */
    public function contractDistribution(): array
    {
        $sql = 'SELECT contract_type, COUNT(*) count FROM offers '
            . 'WHERE contract_type IS NOT NULL AND is_active = 1 '
            . 'GROUP BY contract_type ORDER BY count DESC';
        $rows = $this->pdo->query($sql)->fetchAll();
        return array_map(
            static fn (array $r) => [
                'contract_type' => (string) $r['contract_type'],
                'count' => (int) $r['count'],
            ],
            $rows,
        );
    }

    /**
     * Statistiques de salaires (count / mean / p25 / median / p75 / min / max).
     *
     * @return array<string, int|float|null>
     */
    public function salaryStats(): array
    {
        $values = array_column(
            $this->pdo->query(
                'SELECT salary_min FROM offers WHERE salary_min IS NOT NULL AND is_active = 1 '
                    . 'ORDER BY salary_min ASC'
            )->fetchAll(),
            'salary_min',
        );
        $values = array_map('intval', $values);
        $n = count($values);
        if ($n === 0) {
            return ['count' => 0, 'mean' => null, 'median' => null, 'p25' => null, 'p75' => null, 'min' => null, 'max' => null];
        }
        $pct = static fn (float $p) => $values[min($n - 1, (int) floor($p * ($n - 1)))];
        return [
            'count' => $n,
            'mean' => round(array_sum($values) / $n, 2),
            'median' => $pct(0.5),
            'p25' => $pct(0.25),
            'p75' => $pct(0.75),
            'min' => $values[0],
            'max' => $values[$n - 1],
        ];
    }

    /**
     * Points géographiques agrégés par ville pour la heatmap.
     *
     * @return list<array{city:string, lat:float, lng:float, count:int}>
     */
    public function geoPoints(): array
    {
        $sql = 'SELECT city, lat, lng, COUNT(*) count FROM offers '
            . 'WHERE lat IS NOT NULL AND is_active = 1 '
            . 'GROUP BY city, lat, lng ORDER BY count DESC';
        return array_map(
            static fn (array $r) => [
                'city' => (string) $r['city'],
                'lat' => (float) $r['lat'],
                'lng' => (float) $r['lng'],
                'count' => (int) $r['count'],
            ],
            $this->pdo->query($sql)->fetchAll(),
        );
    }

    /**
     * Timeline des offres publiées sur les N derniers jours.
     *
     * @return list<array{date:string, count:int}>
     */
    public function timeline(int $days = 30): array
    {
        $sql = 'SELECT DATE(posted_at) d, COUNT(*) c FROM offers '
            . 'WHERE posted_at IS NOT NULL AND is_active = 1 '
            . 'AND posted_at >= DATE_SUB(CURDATE(), INTERVAL :d DAY) '
            . 'GROUP BY DATE(posted_at) ORDER BY DATE(posted_at) ASC';
        $stmt = $this->pdo->prepare($sql);
        $stmt->bindValue(':d', $days, PDO::PARAM_INT);
        $stmt->execute();
        return array_map(
            static fn (array $r) => [
                'date' => (string) $r['d'],
                'count' => (int) $r['c'],
            ],
            $stmt->fetchAll(),
        );
    }

    /**
     * Matrice de corrélation des technologies.
     *
     * Pour chaque paire (A, B) où A != B, retourne :
     *  - count    : nombre d'offres actives contenant les deux
     *  - confAB   : P(B|A) = count / offres_avec_A
     *
     * Utilisé pour la heatmap "Si tu vois Python, tu vois aussi Django dans X % des offres".
     *
     * @return array{techs: list<array{name:string, count:int}>, pairs: list<array{a:string,b:string,count:int,conf:float}>}
     */
    public function techCorrelations(int $topN = 12): array
    {
        // Top N technos
        $topStmt = $this->pdo->prepare(
            'SELECT t.display_name, COUNT(DISTINCT ot.offer_id) count '
            . 'FROM technologies t '
            . 'INNER JOIN offer_technologies ot ON ot.technology_id = t.id '
            . 'INNER JOIN offers o ON o.id = ot.offer_id AND o.is_active = 1 '
            . 'GROUP BY t.id '
            . 'ORDER BY count DESC '
            . 'LIMIT :n'
        );
        $topStmt->bindValue(':n', $topN, PDO::PARAM_INT);
        $topStmt->execute();
        $techs = array_map(
            static fn (array $r) => ['name' => (string) $r['display_name'], 'count' => (int) $r['count']],
            $topStmt->fetchAll(),
        );

        if (count($techs) < 2) {
            return ['techs' => $techs, 'pairs' => []];
        }

        $names = array_column($techs, 'name');
        $placeholders = implode(',', array_fill(0, count($names), '?'));

        // Toutes les paires A,B parmi le top (ordre alphabétique garanti pour éviter doublons a-b / b-a)
        $pairsStmt = $this->pdo->prepare(
            'SELECT ta.display_name a, tb.display_name b, COUNT(DISTINCT ota.offer_id) count '
            . 'FROM offer_technologies ota '
            . 'INNER JOIN offer_technologies otb ON ota.offer_id = otb.offer_id AND ota.technology_id != otb.technology_id '
            . 'INNER JOIN technologies ta ON ta.id = ota.technology_id '
            . 'INNER JOIN technologies tb ON tb.id = otb.technology_id '
            . 'INNER JOIN offers o ON o.id = ota.offer_id AND o.is_active = 1 '
            . "WHERE ta.display_name IN ($placeholders) AND tb.display_name IN ($placeholders) "
            . 'GROUP BY ta.id, tb.id'
        );
        $pairsStmt->execute(array_merge($names, $names));

        $countByA = array_column($techs, 'count', 'name');
        $pairs = [];
        foreach ($pairsStmt->fetchAll() as $row) {
            $a = (string) $row['a'];
            $b = (string) $row['b'];
            $count = (int) $row['count'];
            $aTotal = $countByA[$a] ?? 0;
            $pairs[] = [
                'a' => $a,
                'b' => $b,
                'count' => $count,
                'conf' => $aTotal > 0 ? round($count / $aTotal, 3) : 0.0,
            ];
        }

        return ['techs' => $techs, 'pairs' => $pairs];
    }

    /**
     * Top N technologies les plus fréquentes parmi les offres actives.
     *
     * @return list<array{name:string, count:int, category:string}>
     */
    public function topTechnologies(int $n = 10): array
    {
        $sql = 'SELECT t.display_name name, COUNT(DISTINCT ot.offer_id) count, t.category '
            . 'FROM technologies t '
            . 'INNER JOIN offer_technologies ot ON ot.technology_id = t.id '
            . 'INNER JOIN offers o ON o.id = ot.offer_id AND o.is_active = 1 '
            . 'GROUP BY t.id '
            . 'ORDER BY count DESC '
            . 'LIMIT :n';
        $stmt = $this->pdo->prepare($sql);
        $stmt->bindValue(':n', $n, PDO::PARAM_INT);
        $stmt->execute();
        return array_map(
            static fn (array $r) => [
                'name' => (string) $r['name'],
                'count' => (int) $r['count'],
                'category' => (string) $r['category'],
            ],
            $stmt->fetchAll(),
        );
    }
}
