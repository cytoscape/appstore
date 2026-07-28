
    export type RemoteKeys = 'REMOTE_ALIAS_IDENTIFIER/AppConfig';
    type PackageType<T> = T extends 'REMOTE_ALIAS_IDENTIFIER/AppConfig' ? typeof import('REMOTE_ALIAS_IDENTIFIER/AppConfig') :any;