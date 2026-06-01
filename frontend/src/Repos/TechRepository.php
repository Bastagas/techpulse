<?php
/**
 * Repository pour la table `technologies` (pour autocomplete + filtres).
 */

declare(strict_types=1);

namespace TechPulse\Repos;

use PDO;

final class TechRepository
{
    public function __construct(private PDO $pdo)
    {
    }

    /**
     * Liste les technos qui ont au moins `$minOffers` offres associées.
     *
     * @return list<array{canonical_name:string, display_name:string, category:string, count:int}>
     */
    public function listWithCounts(int $minOffers = 1): array
    {
        $sql = 'SELECT t.canonical_name, t.display_name, t.category, '
            . 'COUNT(DISTINCT ot.offer_id) AS count '
            . 'FROM technologies t '
            . 'LEFT JOIN offer_technologies ot ON ot.technology_id = t.id '
            . 'LEFT JOIN offers o ON o.id = ot.offer_id AND o.is_active = 1 '
            . 'GROUP BY t.id '
            . 'HAVING count >= :n '
            . 'ORDER BY count DESC, t.display_name';
        $stmt = $this->pdo->prepare($sql);
        $stmt->bindValue(':n', $minOffers, PDO::PARAM_INT);
        $stmt->execute();
        return array_map(
            static fn (array $r) => [
                'canonical_name' => (string) $r['canonical_name'],
                'display_name' => (string) $r['display_name'],
                'category' => (string) $r['category'],
                'count' => (int) $r['count'],
            ],
            $stmt->fetchAll(),
        );
    }

    /**
     * Recherche pour autocomplete (match partiel sur display_name + canonical_name + aliases).
     *
     * @return list<array{canonical_name:string, display_name:string, count:int}>
     */
    public function search(string $query, int $limit = 10): array
    {
        $query = trim($query);
        if ($query === '') {
            return [];
        }
        $sql = 'SELECT t.canonical_name, t.display_name, '
            . 'COUNT(DISTINCT ot.offer_id) AS count '
            . 'FROM technologies t '
            . 'LEFT JOIN offer_technologies ot ON ot.technology_id = t.id '
            . 'LEFT JOIN offers o ON o.id = ot.offer_id AND o.is_active = 1 '
            . 'WHERE t.display_name LIKE :q1 '
            . 'OR t.canonical_name LIKE :q2 '
            . 'OR JSON_SEARCH(LOWER(t.aliases), \'one\', :q3) IS NOT NULL '
            . 'GROUP BY t.id '
            . 'ORDER BY count DESC, LENGTH(t.display_name), t.display_name '
            . 'LIMIT :limit';
        $stmt = $this->pdo->prepare($sql);
        $like = $query . '%';
        $stmt->bindValue(':q1', $like);
        $stmt->bindValue(':q2', $like);
        $stmt->bindValue(':q3', '%' . strtolower($query) . '%');
        $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmt->execute();
        return array_map(
            static fn (array $r) => [
                'canonical_name' => (string) $r['canonical_name'],
                'display_name' => (string) $r['display_name'],
                'count' => (int) $r['count'],
            ],
            $stmt->fetchAll(),
        );
    }
}
