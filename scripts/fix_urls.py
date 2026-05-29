import os
import re
d = r'g:\[Bengal Bound]\BengalBound-HUB\templates\workspace_admin'
for f in os.listdir(d):
    if f.endswith('.html') and f in ['cms_control.html', 'cms_form.html', 'cms_list.html', 'forum_management.html', 'forum_topic_detail.html']:
        path = os.path.join(d, f)
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Replace {% url 'cms_...'%} or {% url 'forum_...' %} with {% url 'workspace_admin:cms_...' %}
        # Only where the workspace_admin prefix is missing.
        updated_content = re.sub(r"(url\s+')((cms_|forum_)[^\']+)", r"\g<1>workspace_admin:\g<2>", content)

        if updated_content != content:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
            print(f'Updated {f}')
