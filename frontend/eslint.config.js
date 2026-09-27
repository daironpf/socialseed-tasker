import js from '@eslint/js'
import tseslint from 'typescript-eslint'
import pluginVue from 'eslint-plugin-vue'

export default tseslint.config(
  {
    ignores: [
      'dist/**',
      'node_modules/**',
      'coverage/**',
      'playwright-report/**',
      'test-results/**',
      'dataset-de-pruebas/**',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
        extraFileExtensions: ['.vue'],
      },
    },
  },
  {
    files: ['**/*.{ts,vue,js,mjs}'],
    rules: {
      // Type-safety is enforced by vue-tsc; ESLint focuses on code smells
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-unused-vars': 'off',
      'no-undef': 'off',
      // Project conventions
      'vue/multi-word-component-names': 'off',
      'vue/no-v-html': 'off',
      'vue/require-default-prop': 'off',
      'vue/require-explicit-emits': 'off',
      'vue/attributes-order': 'off',
      'vue/order-in-components': 'off',
      'vue/max-attributes-per-line': 'off',
      'vue/singleline-html-element-content-newline': 'off',
      'vue/multiline-html-element-content-newline': 'off',
      'vue/html-self-closing': 'off',
      'vue/html-indent': 'off',
      'vue/html-closing-bracket-newline': 'off',
      'vue/first-attribute-linebreak': 'off',
      'vue/html-button-has-type': 'off',
      'vue/v-on-event-hyphenation': 'off',
      'vue/v-slot-style': 'off',
      'vue/component-tags-order': 'off',
      'vue/block-lang': 'off',
      'vue/no-mutating-props': 'warn',
      'vue/require-toggle-inside-transition': 'off',
    },
  },
  {
    files: ['**/*.spec.ts', '**/*.test.ts', 'e2e/**/*.ts', 'src/test/**/*.ts'],
    rules: {
      '@typescript-eslint/no-require-imports': 'off',
    },
  },
)
