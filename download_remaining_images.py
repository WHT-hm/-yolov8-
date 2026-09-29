#!/usr/bin/env python3
"""
Download remaining pest images using direct URLs from various sources
"""

import os
import requests
import time
from pathlib import Path

# Direct image URLs from reliable sources (Wikimedia, iNaturalist, agricultural sites)
IMAGE_URLS = {
    # Already downloaded (5 images)
    # carposina-sasakii.jpg ✓
    # spodoptera-litura.jpg ✓
    # grapholita-molesta.jpg ✓
    # chilo-suppressalis.jpg ✓
    # jacobiasca-lybica.jpg ✓
    
    # Remaining images (15 needed)
    'icerya-purchasi.jpg': 'https://upload.wikimedia.org/wikipedia/commons/3/3d/Scale_insects_%287244837120%29.jpg',
    'maruca-vitrata.jpg': 'https://inaturalist-open-data.s3.amazonaws.com/observations/observation_photos/5c6da7a5-c1f1-4a0f-8eaa-e4ae58fe4ddd/original.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256',
    'theretra-oldenlandiae.jpg': 'https://upload.wikimedia.org/wikipedia/commons/d/d9/Theretra_oldenlandiae_male.jpg',
    'heliothis-virescens.jpg': 'https://upload.wikimedia.org/wikipedia/commons/e/ed/Heliothis_virescens_%E2%80%93_Tobacco_Budworm_Moth_%2814513506849%29.jpg',
    'manduca-sexta.jpg': 'https://upload.wikimedia.org/wikipedia/commons/2/2e/Manduca_sexta.jpg',
    'ectropis-obliqua.jpg': 'https://upload.wikimedia.org/wikipedia/commons/4/4f/Ectropis_obliqua_NHMUK.jpg',
    'adelphocoris-lineolatus.jpg': 'https://upload.wikimedia.org/wikipedia/commons/9/9e/Noorwijk_-_Luzernesierblindwants_%28Adelphocoris_lineolatus%29.jpg',
    'aphis-gossypii.jpg': 'https://upload.wikimedia.org/wikipedia/commons/2/29/CSIRO_ScienceImage_7331_Aphids_on_cotton.jpg',
    'melanagromyza-sojae.jpg': 'https://upload.wikimedia.org/wikipedia/commons/5/54/Melanagromyza.jpg',
    'myzus-nicotianae.jpg': 'https://upload.wikimedia.org/wikipedia/commons/7/7c/Myzus_persicae_on_potato.jpg',
    'euproctis-pseudoconspersa.jpg': 'https://inaturalist-open-data.s3.amazonaws.com/observations/observation_photos/32a8e5fd-5f85-4d18-897c-87c8a4d1c2b3/original.jpg?X-Amz-Algorithm=AWS4-HMAC-SHA256',
    'empoasca-flavescens.jpg': 'https://upload.wikimedia.org/wikipedia/commons/6/65/Empoasca_vitis_%28macro%29.jpg',
    'nilaparvata-lugens-nymph.jpg': 'https://upload.wikimedia.org/wikipedia/commons/c/ca/Nilaparvata_lugens_-_Brown_planthopper_-_UGA5190055.jpg',
    'sitodiplosis-mosellana.jpg': 'https://upload.wikimedia.org/wikipedia/commons/5/51/Hessian_Fly_2.jpg',
    'rhizoctonia-cerealis.jpg': 'https://upload.wikimedia.org/wikipedia/commons/a/ab/Sharp_eyespot_of_wheat.jpg',
}

def download_image(url, filepath, timeout=15):
    """Download image from URL"""
    try:
        print(f"  Downloading from {url[:60]}...", end='', flush=True)
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            size = os.path.getsize(filepath) / 1024
            print(f" ✓ ({size:.1f} KB)")
            return True
    except Exception as e:
        print(f" ✗ ({str(e)[:40]})")
    return False

def main():
    output_dir = r"D:\pipeline-widget\frontend\public\pest-images"
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 80)
    print("Downloading Remaining Pest Images")
    print("=" * 80)
    print()

    successful = 0
    skipped = 0
    failed = 0

    for filename, url in IMAGE_URLS.items():
        filepath = os.path.join(output_dir, filename)

        # Skip if already exists
        if os.path.exists(filepath):
            size = os.path.getsize(filepath) / 1024
            print(f"✓ {filename} (already exists, {size:.1f} KB)")
            skipped += 1
            continue

        print(f"↓ {filename}")
        if download_image(url, filepath):
            successful += 1
        else:
            failed += 1

        time.sleep(0.5)  # Rate limiting

    print()
    print("=" * 80)
    print(f"Results: {successful} downloaded, {skipped} skipped, {failed} failed")
    print("=" * 80)

if __name__ == '__main__':
    main()
