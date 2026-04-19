# syntax=docker/dockerfile:1.6
# ─────────────────────────────────────────────────────────────
# TechPulse Frontend — PHP 8.2 + Apache
# ─────────────────────────────────────────────────────────────

FROM php:8.2-apache AS base

# git + unzip pour composer, PDO MySQL + opcache
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        unzip \
    && rm -rf /var/lib/apt/lists/* \
    && docker-php-ext-install pdo_mysql opcache \
    && docker-php-ext-enable opcache

# Config Apache : mod_rewrite + docroot
RUN a2enmod rewrite && \
    sed -i 's!/var/www/html!/var/www/html/public!g' /etc/apache2/sites-available/000-default.conf && \
    sed -i 's!/var/www/!/var/www/html/public!g' /etc/apache2/apache2.conf

# Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /var/www/html

# Install deps en premier pour le cache
COPY composer.json composer.lock* ./
RUN composer install --no-dev --no-scripts --no-autoloader --prefer-dist

# Copy app
COPY . .
RUN composer dump-autoload --optimize --no-dev

RUN chown -R www-data:www-data /var/www/html

# Railway injecte $PORT, Apache écoute normalement 80
# → on utilise un script pour brancher le port dynamique
RUN echo '#!/bin/sh\n\
PORT=${PORT:-80}\n\
sed -i "s/Listen 80/Listen $PORT/" /etc/apache2/ports.conf\n\
sed -i "s/:80>/:$PORT>/" /etc/apache2/sites-available/000-default.conf\n\
apache2-foreground' > /usr/local/bin/start.sh && \
    chmod +x /usr/local/bin/start.sh

EXPOSE 80

CMD ["/usr/local/bin/start.sh"]
