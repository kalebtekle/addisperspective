from django import forms

class ItalicizedTextInput(forms.TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        italic_start = '<span style="font-style: italic;">'
        italic_end = '</span>'
        if value:
            if '|italic|' in value:
                parts = value.split('|italic|')
                value = f'{parts[0]}{italic_start}{parts[1]}{italic_end}{parts[2]}'
            return f'<input type="text" name="{name}" value="{value}" />'
        return super().render(name, value, attrs, renderer)
