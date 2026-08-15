interface User {
    readonly name: string;
}

const greet = (user: User): string => `Hello, ${user.name}`;
