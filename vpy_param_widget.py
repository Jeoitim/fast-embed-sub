from PySide6.QtWidgets import QWidget, QFormLayout, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Signal, Qt
from qfluentwidgets import (
    DoubleSpinBox, SpinBox, ComboBox, CheckBox, LineEdit, Slider, BodyLabel,
    CardWidget, SubtitleLabel
)

class SliderWithValue(QWidget):
    valueChanged = Signal()  # 0-parameter signal to connect to param_changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        self.slider = Slider(Qt.Horizontal, self)
        self.label = BodyLabel(self)
        self.label.setMinimumWidth(60)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.label)
        
        self.slider.valueChanged.connect(self.on_value_changed)
        
        self._options = None
        self._is_float = False
        self._float_range = None
        self._float_step = None
        
    def setDiscreteOptions(self, options):
        self._options = [str(o) for o in options]
        self.slider.setRange(0, len(self._options) - 1)
        self.slider.setSingleStep(1)
        
    def setFloatRange(self, min_val, max_val, step):
        self._is_float = True
        self._float_range = (min_val, max_val)
        self._float_step = step
        steps = int(round((max_val - min_val) / step))
        self.slider.setRange(0, steps)
        self.slider.setSingleStep(1)
        
    def setIntRange(self, min_val, max_val, step=1):
        self.slider.setRange(min_val, max_val)
        self.slider.setSingleStep(step)
        
    def setValue(self, value):
        self.slider.blockSignals(True)
        if self._options is not None:
            val_str = str(value)
            if val_str in self._options:
                self.slider.setValue(self._options.index(val_str))
            else:
                self.slider.setValue(0)
        elif self._is_float:
            min_val, max_val = self._float_range
            val = float(value)
            steps = int(round((val - min_val) / self._float_step))
            self.slider.setValue(steps)
        else:
            self.slider.setValue(int(value))
        self.slider.blockSignals(False)
        self.update_label()
        
    def value(self):
        if self._options is not None:
            val_str = self._options[self.slider.value()]
            # Try to convert back to numeric if possible
            try:
                if '.' in val_str:
                    return float(val_str)
                return int(val_str)
            except ValueError:
                return val_str
        elif self._is_float:
            min_val, max_val = self._float_range
            calc = min_val + self.slider.value() * self._float_step
            step_str = str(self._float_step)
            decimals = len(step_str.split('.')[1]) if '.' in step_str else 2
            return round(calc, decimals)
        else:
            return self.slider.value()
            
    def on_value_changed(self, val):
        self.update_label()
        self.valueChanged.emit()
        
    def update_label(self):
        self.label.setText(str(self.value()))


class VpyPresetParamWidget(QWidget):
    param_changed = Signal()
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(24) # Card spacing matching Home page
        
        self.widgets = {}
        self.param_metadata = {}
 
    def clear_params(self):
        """清空所有动态生成的控件"""
        for i in reversed(range(self.main_layout.count())):
            item = self.main_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
        self.widgets.clear()
        self.param_metadata.clear()
 
    def load_params(self, parameters):
        """根据解析出的参数元数据渲染控件列表"""
        self.clear_params()
        if not parameters:
            self.hide()
            return
            
        self.show()
        
        # 1. 整理分组
        grouped = {}
        for param in parameters:
            g_name = param.get("group", "常规设置")
            if g_name not in grouped:
                grouped[g_name] = []
            grouped[g_name].append(param)
            
        # 2. 组内排序并生成界面
        for g_name, items in grouped.items():
            items.sort(key=lambda x: x.get("order", 999))
            
            # 创建 CardWidget 替换 QGroupBox，确保和主页风格排版一致
            card = CardWidget()
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(20, 20, 20, 20)
            card_layout.setSpacing(16)
            
            # 使用 SubtitleLabel 作为分组标题，对应主页的“媒体与字幕源”级别
            group_title_lbl = SubtitleLabel(g_name)
            card_layout.addWidget(group_title_lbl)
            
            # 组内参数表单
            form_layout = QFormLayout()
            form_layout.setSpacing(16)
            form_layout.setLabelAlignment(Qt.AlignLeft)
            
            for param in items:
                pid = param.get("id")
                pname = param.get("name", pid)
                ptype = param.get("type", "text")
                default = param.get("default")
                tooltip = param.get("tooltip", "")
                
                self.param_metadata[pid] = param
                
                # 创建控件
                widget = None
                if ptype == "float":
                    w = DoubleSpinBox()
                    rng = param.get("range", [0.0, 100.0])
                    w.setRange(rng[0], rng[1])
                    w.setDecimals(param.get("decimals", 2))
                    w.setSingleStep(0.1)
                    w.setValue(float(default) if default is not None else rng[0])
                    w.valueChanged.connect(lambda: self.param_changed.emit())
                    widget = w
                elif ptype == "integer":
                    w = SpinBox()
                    rng = param.get("range", [0, 100])
                    w.setRange(rng[0], rng[1])
                    w.setValue(int(default) if default is not None else rng[0])
                    w.valueChanged.connect(lambda: self.param_changed.emit())
                    widget = w
                elif ptype == "select" or ptype == "selectbox":
                    w = ComboBox()
                    opts = param.get("options", [])
                    w.addItems([str(o) for o in opts])
                    if default is not None:
                        idx = w.findText(str(default))
                        if idx != -1: w.setCurrentIndex(idx)
                    w.currentIndexChanged.connect(lambda: self.param_changed.emit())
                    widget = w
                elif ptype == "bool":
                    w = CheckBox()
                    w.setChecked(bool(default))
                    w.stateChanged.connect(lambda: self.param_changed.emit())
                    widget = w
                elif ptype in ("slider", "slidebar"):
                    w = SliderWithValue()
                    opts = param.get("options")
                    if opts:
                        w.setDiscreteOptions(opts)
                    else:
                        rng = param.get("range", [0, 100])
                        step = param.get("step")
                        is_float = (
                            isinstance(rng[0], float) or 
                            isinstance(rng[1], float) or 
                            isinstance(step, float) or
                            param.get("decimals") is not None
                        )
                        if is_float:
                            st = float(step) if step is not None else 0.01
                            w.setFloatRange(float(rng[0]), float(rng[1]), st)
                        else:
                            st = int(step) if step is not None else 1
                            w.setIntRange(int(rng[0]), int(rng[1]), st)
                            
                    w.setValue(default if default is not None else (opts[0] if opts else rng[0]))
                    w.valueChanged.connect(lambda: self.param_changed.emit())
                    widget = w
                else: # text / inputbox / input
                    w = LineEdit()
                    w.setText(str(default) if default is not None else "")
                    w.textChanged.connect(lambda: self.param_changed.emit())
                    widget = w
                    
                if widget:
                    if tooltip:
                        widget.setToolTip(tooltip)
                    self.widgets[pid] = widget
                    lbl = BodyLabel(pname)
                    form_layout.addRow(lbl, widget)
                    
            card_layout.addLayout(form_layout)
            self.main_layout.addWidget(card)
 
    def get_values(self):
        """返回当前的参数字典"""
        values = {}
        for pid, widget in self.widgets.items():
            meta = self.param_metadata.get(pid, {})
            ptype = meta.get("type", "text")
            
            if ptype == "float" or ptype == "integer":
                values[pid] = widget.value()
            elif ptype in ("slider", "slidebar"):
                values[pid] = widget.value()
            elif ptype == "select" or ptype == "selectbox":
                values[pid] = widget.currentText()
            elif ptype == "bool":
                values[pid] = widget.isChecked()
            else:
                values[pid] = widget.text()
        return values

    def reset_defaults(self):
        """将所有控件恢复为默认值"""
        for pid, widget in self.widgets.items():
            meta = self.param_metadata.get(pid, {})
            default = meta.get("default")
            ptype = meta.get("type", "text")
            
            if default is None:
                continue
                
            if ptype == "float" or ptype == "integer":
                widget.setValue(float(default) if ptype == "float" else int(default))
            elif ptype in ("slider", "slidebar"):
                widget.setValue(default)
            elif ptype == "select" or ptype == "selectbox":
                idx = widget.findText(str(default))
                if idx != -1:
                    widget.setCurrentIndex(idx)
            elif ptype == "bool":
                widget.setChecked(bool(default))
            else:
                widget.setText(str(default))
