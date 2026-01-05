from argparse import ArgumentParser

from src.sql_agent.rag.sql_rag import sql_retriever

def main():
    """Main function for sql ingestion on singleton qrant client of `sql_retriever`"""
    
    parser = ArgumentParser(description="Load vector data in SQL-RAG system.")

    parser.add_argument('--collection', default="nl_to_sql", help="Qdrant collection name.")
    parser.add_argument('--update', action="store_true", default=False, help="Update collection with new vectors.")
    parser.add_argument('--rebuild', action="store_true", default=False, help="Rebuild the whole collection.")
    parser.add_argument('--create', action="store_true", default=False, help="Create a new collection.")
    parser.add_argument('--delete', action="store_true", default=False, help="Delete the specified collection.")
    parser.add_argument('--view', action="store_true", default=False, help="Get some stats of the existing collections.")

    args = parser.parse_args()

    if args.rebuild:
        sql_retriever.create_collection(args.collection, force_rebuild=True)
        sql_retriever.embed()
        return

    if args.update:
        sql_retriever.update_collection(args.collection)
        return

    if args.create:
        sql_retriever.create_collection(args.collection)
        return

    if args.delete:
        if args.collection == "nl_to_sql": 
            print("Cannot delete default collection `nl_to_sql`. Please, try rebuild though.")

        else:
            sql_retriever.qclient.delete_collection(args.collection)
            print(f"Collection `{args.collection}` deleted.")

    if args.view:
        collections = sql_retriever.qclient.get_collections().collections
        print()
        for j, collection in enumerate(collections, start=1):
            info = sql_retriever.qclient.get_collection(collection.name)
            stats = info.model_dump()
            v_cfg = stats.get("config", {}).get("params", {}).get("vectors", {})
            points_count = stats.get("points_count")
            print(f" Collection {j}:\t name=`{collection.name}`\n\t\t #points={points_count}\n\t\t vectors_dim={v_cfg.get("size")}\n\t\t metric={v_cfg.get("distance")}\n\t\t payload_on_disk={v_cfg.get("on_disk_payload")}\n")

        return

if __name__=="__main__":
    main()