"""Offline account administration; no network or API endpoint is exposed."""
import argparse
from .accounts import create_account_file, update_account_file


def main(argv=None):
    parser = argparse.ArgumentParser(description='Manage local RoadScan account tokens offline')
    parser.add_argument('--file', required=True, help='Private account JSON path (outside Git)')
    commands = parser.add_subparsers(dest='action', required=True)
    create = commands.add_parser('init', help='Create first account file')
    create.add_argument('--username', required=True)
    create.add_argument('--role', choices=['admin'], default='admin')
    add = commands.add_parser('add', help='Create additional account')
    add.add_argument('--username', required=True)
    add.add_argument('--role', required=True, choices=['admin', 'reviewer', 'viewer'])
    revoke = commands.add_parser('revoke', help='Immediately invalidate an account token')
    revoke.add_argument('--username', required=True)
    rotate = commands.add_parser('rotate', help='Replace an account token without changing its role')
    rotate.add_argument('--username', required=True)
    args = parser.parse_args(argv)
    if args.action == 'init':
        token = create_account_file(args.file, args.username, args.role)
    elif args.action == 'rotate':
        from .accounts import rotate_account_token
        token = rotate_account_token(args.file, args.username)
    else:
        token = update_account_file(args.file, args.action, args.username, getattr(args, 'role', None))
    if token:
        print('New token (shown once; store securely):', token)
    else:
        print('Account revoked')


if __name__ == '__main__':
    main()
