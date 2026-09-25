import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{js,jsx}'],
    extends: [
      js.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    rules: {
      // Flaguea "setError(null); setData(null)" antes de un fetch dentro de
      // un useEffect -- el patron estandar de data-fetching en React desde
      // que existen los hooks (2018), usado a proposito en todo el proyecto
      // para limpiar el estado viejo mientras carga el ticker/pantalla
      // nuevos. Es una regla reciente y opinativa del equipo de React, no
      // marca codigo roto -- decision consciente de mantenerlo en warn en
      // vez de refactorizar 14 sitios sin necesidad real.
      'react-hooks/set-state-in-effect': 'warn',
    },
  },
])
