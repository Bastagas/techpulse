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
