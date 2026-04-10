import os

ui_file = os.path.join(os.path.dirname(__file__), 'SZ_edu.ui')
with open(ui_file, 'rb') as f:
    content = f.read().decode('utf-8')

target = """            <item><property name="text"><string>Decision Trees (DT)</string></property></item>
           </widget>
          </item>
         </layout>"""

replacement = """            <item><property name="text"><string>Decision Trees (DT)</string></property></item>
           </widget>
          </item>
          <item><widget class="QLabel" name="lbl_cl_r_title">
           <property name="text"><string>Classify SI</string></property>
           <property name="font"><font><bold>true</bold></font></property>
          </widget></item>
          <item>
           <widget class="QListWidget" name="classify_list_r">
            <item><property name="text"><string>Classify Raster by ROC</string></property></item>
            <item><property name="text"><string>ROC Generator</string></property></item>
            <item><property name="text"><string>Confusion Matrix (FP/TN Threshold)</string></property></item>
           </widget>
          </item>
         </layout>"""

# Fix line endings
target = target.replace('\n', '\r\n')
replacement = replacement.replace('\n', '\r\n')

if target in content:
    content = content.replace(target, replacement)
    with open(ui_file, 'wb') as f:
        f.write(content.encode('utf-8'))
    print("UI file updated successfully!")
else:
    print("Target not found in UI file.")
