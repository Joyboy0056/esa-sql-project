# USAGE: python -m scripts.create_postgres --help
from argparse import ArgumentParser

from src.ingestion.loader import STACLoader
from build.config import config

def main(bbox: list=config.DEFAULT_BOX):
    """Main function for db creation script, with default bbox in Umbria/Lazio"""

    parser = ArgumentParser(description='Load ESA Sentinel data')
    parser.add_argument(
        '--bbox', # nargs=4, 
        default=bbox,
        type=float, 
        required=False,
        help='Bounding box: min_lon min_lat max_lon max_lat'
    )
    parser.add_argument('--start', required=False, help='Start date YYYY-MM-DD')
    parser.add_argument('--end', required=False, help='End date YYYY-MM-DD')
    parser.add_argument('--limit', type=int, default=500, help='Max scenes')
    parser.add_argument('--update', action='store_true', help='Update up to today data')
    
    args = parser.parse_args()
    
    loader = STACLoader()

    if args.update:
        loader.update_data(bbox=args.bbox)

    else:
        loader.load_region(
            bbox=args.bbox,
            datetime_range=f"{args.start}T00:00:00Z/{args.end}T23:59:59Z",
            limit=args.limit
        )
    loader.print_stats()
    

if __name__ == "__main__":
    main()    