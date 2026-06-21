<?php
/**
 * Plugin Name: Almoxarifado - Ajustes CSS
 * Description: Ajusta largura e cores do Almoxarifado para o tema FOB
 * Version: 1.0
 */
add_action('wp_head', function () {
    ?><style>
#az .ct{max-width:100%!important}
#az .wr{overflow-x:auto!important;max-width:100%!important}
#az td{word-break:break-word!important}
#az .hdr{background:linear-gradient(135deg,#055e6f,#1094ab)!important}
#az h2{color:#1094ab!important}
#az .sc .n{color:#1094ab!important}
#az .bt{background:#1094ab!important}
#az .bt:hover{background:#055e6f!important}
#az .bt-o{color:#1094ab!important;border-color:#1094ab!important}
#az th{color:#055e6f!important}
</style><?php
});
