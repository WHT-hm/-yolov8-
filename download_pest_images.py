#!/usr/bin/env python3
"""
Batch download pest images from iNaturalist API and other sources
Uses iNaturalist's official API which doesn't restrict automated access
"""

import os
import json
import requests
from pathlib import Path
import time

# Map of pest filenames to iNaturalist taxon IDs
PEST_TAXA = {
    'carposina-sasakii': 416959,  # Peach fruit borer
    'spodoptera-litura': 124875,  # Black cutworm moth
    'grapholita-molesta': 401850,  # Oriental fruit moth
    'maruca-vitrata': 383048,  # Legume pod borer
    'theretra-oldenlandiae': 401763,  # Oleander hawkmoth
    'heliothis-virescens': 401807,  # Tobacco budworm
    'manduca-sexta': 123978,  # Tobacco hornworm
    'ectropis-obliqua': 408177,  # Tea geometrid
    'chilo-suppressalis': 401813,  # Rice stem borer
    'adelphocoris-lineolatus': 383044,  # Cotton mirid
    'aphis-gossypii': 127177,  # Cotton aphid
    'jacobiasca-lybica': 401812,  # Cotton leafhopper
}

# Wikimedia Commons direct URLs (these work reliably)
WIKIMEDIA_IMAGES = {
    'spodoptera-litura': 'https://commons.wikimedia.org/wiki/Special:FilePath/Spodoptera_litura.jpg',
    'heliothis-virescens': 'https://commons.wikimedia.org/wiki/Special:FilePath/Heliothis_virescens_%E2%80%93_Tobacco_Budworm_Moth_(14513506849).jpg',
    'manduca-sexta': 'https://commons.wikimedia.org/wiki/Special:FilePath/Tobacco_Hornworm_1.jpg',
    'nilaparvata-lugens-nymph': 'https://commons.wikimedia.org/wiki/Special:FilePath/Nilaparvata_lugens_-_Brown_planthopper_-_UGA5190055.jpg',
    'sitodiplosis-mosellana': 'https://commons.wikimedia.org/wiki/Special:FilePath/Hessian_Fly.jpg',
    'adelphocoris-lineolatus': 'https://commons.wikimedia.org/wiki/Special:FilePath/Noorwijk_-_Luzernesierblindwants_(Adelphocoris_lineolatus).jpg',
    'aphis-gossypii': 'https://commons.wikimedia.org/wiki/Special:FilePath/CSIRO_ScienceImage_7331_Aphids_on_cotton_7.jpg',
}

def get_inaturalist_photo_url(taxon_id):
    """Get the first observation photo URL for a taxon from iNaturalist API"""
    try:
        # Query iNaturalist API for observations with photos
        url = f"https://api.inaturalist.org/v1/observations"
        params = {
            'taxon_id': taxon_id,
            'has_photos': True,
            'per_page': 1,
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('results') and len(data['results']) > 0:
                observation = data['results'][0]
                if observation.get('photos') and len(observation['photos']) > 0:
                    photo = observation['photos'][0]
                    # Return the medium-sized image URL
                    if 'url' in photo:
                        return photo['url'].replace('square', 'medium')
    except Exception as e:
        print(f"  Error querying iNaturalist for taxon {taxon_id}: {e}")

    return None

def download_image(url, filepath, timeout=15):
    """Download image from URL to filepath"""
    try:
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"  Error downloading from {url}: {e}")

    return False

def main():
    output_dir = r"D:\pipeline-widget\frontend\public\pest-images"

    # Create directory if needed
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 70)
    print("Pest Image Downloader - Using iNaturalist API and Wikimedia Commons")
    print("=" * 70)
    print()

    successful = 0
    failed = 0

    # Try Wikimedia Commons images first (most reliable)
    print("Downloading from Wikimedia Commons...")
    print("-" * 70)
    for filename, url in WIKIMEDIA_IMAGES.items():
        filepath = os.path.join(output_dir, f"{filename}.jpg")
        if os.path.exists(filepath):
            print(f"✓ {filename}.jpg (already exists)")
            successful += 1
            continue

        print(f"↓ {filename}.jpg... ", end='', flush=True)
        if download_image(url, filepath, timeout=20):
            file_size = os.path.getsize(filepath) / 1024
            print(f"✓ ({file_size:.1f} KB)")
            successful += 1
        else:
            print("✗ Failed")
            failed += 1

        time.sleep(0.5)  # Rate limiting

    print()
    print("Downloading from iNaturalist API...")
    print("-" * 70)
    for filename, taxon_id in PEST_TAXA.items():
        filepath = os.path.join(output_dir, f"{filename}.jpg")
        if os.path.exists(filepath):
            print(f"✓ {filename}.jpg (already exists)")
            successful += 1
            continue

        print(f"↓ {filename}.jpg ({taxon_id})... ", end='', flush=True)
        photo_url = get_inaturalist_photo_url(taxon_id)

        if photo_url and download_image(photo_url, filepath):
            file_size = os.path.getsize(filepath) / 1024
            print(f"✓ ({file_size:.1f} KB)")
            successful += 1
        else:
            print("✗ No photo found or download failed")
            failed += 1

        time.sleep(1)  # Respect API rate limits

    print()
    print("=" * 70)
    print(f"Results: {successful} downloaded/found, {failed} failed")
    print("=" * 70)

    if failed > 0:
        print()
        print("Note: For failed downloads, visit the links in IMAGE_DOWNLOAD_GUIDE.md")
        print("      and manually download those images.")

if __name__ == '__main__':
    main()
