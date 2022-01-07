module.exports = {
  env: {
    browser: true,
    es6: true,
    node: true,
  },
  extends: ["eslint:recommended", "prettier"],
  parserOptions: {
    ecmaVersion: 2018,
  },
  rules: {
    "linebreak-style": ["error", "unix"],
    "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    quotes: 0,
  },
}
