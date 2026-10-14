export default {
	betuiSpin: {
		type: 'sprite',
		src: 'assets/midnight-lounge/ui/betui/betui_spin_button_midnight_lounge.png',
		preload: false,
	},
	betuiBuyBonus: {
		type: 'sprite',
		src: 'assets/skyjump_v2/ui/betui/betui_buy_bonus_button.png',
		preload: false,
	},
	betuiAuto: {
		type: 'sprite',
		src: 'assets/midnight-lounge/ui/betui/betui_auto_button_midnight_lounge.png',
		preload: false,
	},
	betuiTurbo: {
		type: 'sprite',
		src: 'assets/midnight-lounge/ui/betui/betui_turbo_button_midnight_lounge.png',
		preload: false,
	},
	betuiMenu: {
		type: 'sprite',
		src: 'assets/skyjump_v2/ui/betui/betui_menu_button.png',
		preload: false,
	},
	betuiTile: {
		type: 'sprite',
		src: 'assets/skyjump_v2/ui/betui/betui_background_tile.png',
		preload: false,
	},
	betuiPlus: {
		type: 'sprite',
		src: 'assets/skyjump_v2/ui/betui/betui_btn_plus.png',
		preload: false,
	},
	betuiMinus: {
		type: 'sprite',
		src: 'assets/skyjump_v2/ui/betui/betui_btn_minus.png',
		preload: false,
	},
	betuiStop: {
		type: 'sprite',
		src: 'assets/midnight-lounge/ui/betui/betui_stop_button_midnight_lounge.png',
		preload: false,
	},
	betuiLanguage: {
		type: 'sprite',
		src: 'assets/skyjump_v2/ui/betui/betui_language_button.png',
		preload: false,
	},
	betuiSoundOff: {
		type: 'sprite',
		src: 'assets/skyjump_v2/ui/betui/betui_sound_off_button.png',
		preload: false,
	},
	betuiSoundOn: {
		type: 'sprite',
		src: 'assets/skyjump_v2/ui/betui/betui_sound_on_button.png',
		preload: false,
	},
	betuiInfo: {
		type: 'sprite',
		src: 'assets/skyjump_v2/ui/betui/betui_info_button.png',
		preload: false,
	},
	betuiPaytable: {
		type: 'sprite',
		src: 'assets/skyjump_v2/ui/betui/betui_paytable_button.png',
		preload: false,
	},
	betuiSettings: {
		type: 'sprite',
		src: 'assets/skyjump_v2/ui/betui/betui_settings_button.png',
		preload: false,
	},
	betuiMenuExit: {
		type: 'sprite',
		src: 'assets/skyjump_v2/ui/betui/betui_menu_exit_button.png',
		preload: false,
	},
	sound: {
		type: 'audio',
		src: new URL('../../static/assets/audio/sounds.json', import.meta.url).href,
		preload: true,
	},
} as const;
