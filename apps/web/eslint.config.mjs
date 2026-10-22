import {defineConfig, globalIgnores} from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTypescript from 'eslint-config-next/typescript';

const noUiLiterals = {
  meta:{type:'problem',schema:[],messages:{literal:'El texto visible debe proceder de messages/es.json mediante next-intl.'}},
  create(context) {
    return {
      JSXText(node) { if (node.value.trim()) context.report({node,messageId:'literal'}); },
      JSXAttribute(node) {
        if (['aria-label','title','placeholder','alt'].includes(node.name.name) && node.value?.type === 'Literal' && node.value.value) context.report({node,messageId:'literal'});
      },
      JSXExpressionContainer(node) {
        if (node.expression.type === 'Literal' && typeof node.expression.value === 'string' && node.expression.value.trim() && node.parent.type !== 'JSXAttribute') context.report({node,messageId:'literal'});
      }
    };
  }
};
export default defineConfig([
  ...nextVitals,
  ...nextTypescript,
  {files:['app/**/*.tsx','components/**/*.tsx'],ignores:['**/*.test.tsx'],plugins:{studio:{rules:{'no-ui-literals':noUiLiterals}}},rules:{'studio/no-ui-literals':'error'}},
  globalIgnores(['.next/**','next-env.d.ts'])
]);

