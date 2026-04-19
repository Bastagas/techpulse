"""Parsers — normalisation + extraction depuis des données brutes."""

from techpulse_scraper.parsers.location_parser import ParsedLocation, parse_location
from techpulse_scraper.parsers.remote_parser import detect_remote_policy
from techpulse_scraper.parsers.salary_parser import ParsedSalary, parse_salary
from techpulse_scraper.parsers.tech_extractor import ExtractedTech, TechExtractor

__all__ = [
    "ExtractedTech",
    "ParsedLocation",
    "ParsedSalary",
    "TechExtractor",
    "detect_remote_policy",
    "parse_location",
    "parse_salary",
]
