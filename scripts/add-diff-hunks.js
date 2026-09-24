const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, '..', 'frontend', 'dataset-de-pruebas', 'issues.json');
const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

const diffTemplates = {
  CREATED: (filepath) => {
    const ext = filepath.split('.').pop() || 'txt';
    const lang = ext === 'vue' ? 'vue' : ext === 'ts' ? 'typescript' : ext === 'js' ? 'javascript' : ext === 'py' ? 'python' : ext === 'json' ? 'json' : ext === 'css' ? 'css' : ext === 'html' ? 'html' : 'text';
    return {
      language: lang,
      diff_hunk: `@@ -0,0 +1,15 @@\n+import { ref, computed } from 'vue'\n+import { useI18n } from 'vue-i18n'\n+\n+const { t } = useI18n()\n+\n+interface Props {\n+  title: string\n+  description?: string\n+}\n+\n+const props = defineProps<Props>()\n+\n+const isVisible = ref(false)\n+const toggle = () => { isVisible.value = !isVisible.value }\n+export default { isVisible, toggle }`
    };
  },
  EDITED: (filepath) => {
    const ext = filepath.split('.').pop() || 'txt';
    const lang = ext === 'vue' ? 'vue' : ext === 'ts' ? 'typescript' : ext === 'js' ? 'javascript' : ext === 'py' ? 'python' : ext === 'json' ? 'json' : ext === 'css' ? 'css' : ext === 'html' ? 'html' : 'text';
    return {
      language: lang,
      diff_hunk: `@@ -15,7 +15,9 @@\n export function processData(data: Input) {\n-  return transform(data)\n+  const validated = validateInput(data)\n+  if (!validated) throw new Error("Invalid input")\n+  return transform(data)\n }\n \n-export function validate(data: unknown): boolean {\n-  return !!data\n+export function validate(data: unknown): data is Input {\n+  return data !== null && data !== undefined\n }`
    };
  },
  DELETED: (filepath) => {
    const ext = filepath.split('.').pop() || 'txt';
    const lang = ext === 'vue' ? 'vue' : ext === 'ts' ? 'typescript' : ext === 'js' ? 'javascript' : ext === 'py' ? 'python' : ext === 'json' ? 'json' : ext === 'css' ? 'css' : ext === 'html' ? 'html' : 'text';
    return {
      language: lang,
      diff_hunk: `@@ -1,12 +0,0 @@\n-import { oldHelper } from './old-helper'\n-import legacyUtil from './legacy'\n-\n-export function deprecatedFunction() {\n-  console.log('This function is deprecated')\n-  return legacyUtil.doWork()\n-}\n-\n-export const OLD_CONSTANT = 'should be removed'\n-\n-// This entire file is deprecated\n-// Use new-helper.ts instead`
    };
  }
};

let updatedCount = 0;
for (const issue of data.issues) {
  if (issue.affected_files && Array.isArray(issue.affected_files)) {
    for (const file of issue.affected_files) {
      if (!file.diff_hunk) {
        const template = diffTemplates[file.change_type] || diffTemplates.EDITED;
        const result = template(file.path);
        file.diff_hunk = result.diff_hunk;
        file.language = result.language;
        updatedCount++;
      }
    }
  }
}

fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
console.log(`Updated ${updatedCount} affected files with diff_hunk data`);
