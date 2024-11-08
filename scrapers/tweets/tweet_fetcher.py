import requests
import os
import yaml
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
import logging
import json
from tweet_service import setup_logging, ensure_data_directory, save_all_tweets, create_tweet_query

def load_config():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(dir_path, 'tweet_fetcher_config.yaml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def save_state(state, api_calls_count, records_fetched, all_tweets):
    state_data = {
        'last_known_state': state,
        'api_calls_count': api_calls_count,
        'records_fetched': records_fetched,
        'all_tweets_sample': all_tweets[:7]  # Guarda una muestra de los primeros 10 tweets para visibilidad
    }
    with open('last_known_state_detailed.json', 'w') as f:
        json.dump(state_data, f, indent=4)

def load_state():
    try:
        with open('last_known_state_detailed.json', 'r') as f:
            return json.load(f).get('last_known_state', {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def exponential_backoff(attempt, base=60):
    return base * (2 ** attempt)  # Backoff exponencial: retraso base * 2^intento

def fetch_tweets(config):
    start_date = datetime.strptime(config['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(config['end_date'], '%Y-%m-%d').date()
    days_per_iteration = config['days_per_iteration']

    # Lista de cuentas de Twitter de los equipos de La Liga 2024-2025
    accounts = [
        'NEARMobile_app', #nearmobile.app #nearmobile #nearmobileapp #wallet #nearwallet #noncustodial #selfcustodial #peersyst
        'NEARMintern', #intern #NEARMobile #dapps
        'nearblocks', #explorer #blocks #onchain #data #explore #nearblock #txhash #transactions
        'NEARProtocol', #nearprotocol #near #nearfoundation #illia #news
        'finance_ref',#ref #reffinance #dapp #swap #pools #liquiditypools #trade #amm #amms #usdc #usdt #frax #top #tvl
        'ref_intern', #ref #intern #dapp #swap #pools #liquiditypools #trade #amm #amms #usdc #usdt #frax #top #tvl
        'meta_pool', #pool #pools #stake #stNEAR #mpDAO #dao #reStake #liquid #tvl #dapp
        'burrow_finance', #lending #lend #borrow #burrow #usdc #usdt #frax #stake #pools #tvl #dapp
        'beepopula', #community #dapp #privacy #onchain #social
        'DeltaBotTeam', #dca #trade #gachapon #airdrop #swing #bots #ai #stablecoin #usdc #usdt #aibot #tradebot #tokens #auto #dapp
        'shitzuonnear', #dogshit #shitzu #meme #stake #validator #dev #build
        'memedotcooking', #meme #memecoin #launchpad #buy #sell #rug #meme.cooking #cook #memecooking #shitzu #dogshit
        'sharddog', #nft #nfts #mint #sharddog #community #build
        'nadabots', #certificate #did #proof #humanproof #id #bots #nada
        'potlock_', #funding #ai #design #potlock #pot #startup
        'JumpDeFi', #jump #defi #stake #nft
        'TokenBridgeApp', #bridge #swap #transfer #crosschain #solana #binance #arbitrum #token
        'tknhomes', #token #marketplace #launchpad #meme #memecoin
        'NEARDevHub', #dev #build #ai #chain #onnear #devrel #tutorial
        'NEARdevs', #dev #build #ai #chain #onnear
        'ilblackdragon', #founder #illia #dev #build #nearceo #boss #blackdragon #nearprotocol #nearfoundation
        'GNearAi', #meme #ai
        'vxyz_near', #community
        'NEARQuant', #community #news #alpha
        'taostats', #ai #bittensor #masaAI #web3
        'nearcatalog', #community #dapps #dappradar #projects #news #trends
        'marior_dev', #community #dev #shitzu #orderly #futures #derivatives
        'SKYTONET_', #community #mod #ambassador #ref #shitzu #meme #memedotcooking
        'invokerlabs', #dev #build #nearblocks
        'Nearsend_io', #dev #nep #send #invokerlabs #bulk #transactions
        'questflow', #project #dapp #ai #agents
        'DayTrader888', #growth #veax #dex #degen
        'NearKatToken', #meme #memecoin #token #kat #cat
        'ai_pgf', #potlock #ai #funding #agi
        'hotdao_', #hot #herewallet #dao #telegram
        'p_volnov', #hotdao #herewallet #founder #dev
        'ThunderHoodlab', #meme #dex #marketplace #launchpad #trade #deploy
        'getmasafi', #ai #agents #scrape #data #twitterscrape #discord #telegram #web #webscrape #mine #bittensor #tao
        'growthmate_xyz', #data #onchain #dapps #trends #community
        'NearGamesDAO', #community #game #gamers #dao #play
        'SailGPESP', #sailgp #nearspain #nearesp #nearpartners #nearsports
        'elm_money', #founder #ai #community #neardc #digital #marketing #dao #aurora #apps #games
        'KagemniKarimu', #dev #devrel #lava #magma #lavanet #rpc #data #apps #host #storage
        'xgilxgil', #dev #lava #lavanet #rpc #magma
        'magmadevs', #dev #lava #lavanet #magma
        'consensus128', #marketing #community #lava #rpc
        'theinterestedr1', #founder #cto #lava #dev #build
        'NimrodxLava', #dev #lava #r&d #magma
        'beanonnear', #meme #memecoin #token #mrbean #stake #nft #ref #jump
        'fraxfinance', #stable #coin #token #lend #borrow #defi #fiat #stake #sfrax
        '_Curmello', #community #designer #graphic #content #creator #cm #news
        'intelnear', #meme #memecoins #token #ai #intel
        'near_ai', #ai #machine #code #dev
        'pauldgreat1234', #otto #nigeria #octopus #omni #dfinity #btc #uwon
        'Ottochain_', #otto #token #omnity #evm #cosmos #cosmossdk
        'OctopusNation_', #octopus #network #restake #stake #cosmos #cosmossdk
        'nearuaguild', #ukraine #ucrania #nearuaguild #dev #community #nation
        'i_moskalenko_', #ukraine #uaguild #community #content #creator
        'inscriptionneat', #neat #token #supportedtoken #ai #inscription #rollup #scale
        'buidlnear', #vikthebuilder #dev #components #nearprotocol #bitte
        'David___Mo', #nearprotocol #nearfoundation #creative #marketing #campaign #strategy #davidmo
        'Waliyullah99', #spaces #spacehost #host #chill #xspace
        'ChillonNear', #meme #memecoin #chill #token
        'near_punks', #punks #nfts #nft #largestNFTcollection #npunks #nearkingdoms
        'nearkingdoms', #game #nft #gaming #nearkingdoms #nearpunks #punks
        'maxtonear', #founder #nearpunks #nearkingdoms #game #punks #nft #nfts #dev
        'near_brazil', #community #brazil #brasil #news #portugues #noticias #latam
        'NearlendDao', #capitalmarket #dao #defi #lending #lend #stake #apy #liquidation #stablecoins
        'NEARArgentina', #argentina #latam #community #news #español #comunidad
        'Near_ES', #españa #español #latam #community #news #comunidad
        'Milly_R06', #españa #latam #español #news #cm
        'Freyja_GoddessM', #women #nearwomen #womenweb3
        'NearGlobeDAO', #nations #world #nearregional #communities #countries #globe #nearglobe
        'ThaLeonard_', #cm #projectmanager #marketing #strategy #neardc #freelancers #nearprotocol #community
        'NearHausaa', #nation #community #hausaa #language #nigeria
        'USM_eme', #meme #memecoin #token #usm
        'Lonkonnear', #meme #lonk #memecoin #token
        'theomnidao', #build #nft #nearprotocol #omni #dao #nearfoundation
        'dragonisnear', #meme #memecoin #blackdragon #dragon #token
        'dragonbot_xyz', #meme #memecoin #telegram #bot #token
        'LuloBank', #mint #nearmint #lulo #lulox #stablecoin #token #minter #nep141 #dev #colombia #latam
        'NearMexico', #mexico #latam #community #nation #news
        'srpuuul', #memes #intern #metapool #stNEAR #mpDAO #meta_pool
        'stakecito', #cosmos #validator #cosmossdk #delegator
        'staderlabs', #st #token #neartoken #stader #stake #liquidstake #liquid
        'Masi_DN', #dev #build #onchain #data #news
        'NearnftWG', #nft #nearnft #nftwork #nftworkgroup #neardc #sharddog #nearverse
        'SatJanserik1986', #community #news #jsat
        'ThePiVortex', #owen #neardevrel #dev #devrel #community #news #build #xspace
        'pikespeak_ai', #dev #explorer #pikespeak #ai #build #onchain
        'ekuzyakov', #evgeny #founder #fastnear #nearsocial #social #nearprotocol #proximity #labs #dev #build
        'fast_near', #infra #rpc #api #dev #build
        'proximityfi', #dev #learn #build #ai #chainsignatures #chainabstraction #sighnatures #abstraction
        'zacodil', #community #news #ai #dev #zavodil #validator #vadim #infra
        'sal_data', #dev #data #stake #nearprotocol #onchain #build #ambassador #community
        'MeteorWallet', #wallet #competition #meteor
        'TheChels001', #mitte #nft #community #ambassador #content
        'GUS_DAO', #nearweek #week #news #community #dao #linkdrop #openweb #gus
        'Rous_cripto', #latam #metapool #argentina #content #community #intern #customersupport #spaces #xspaces
        'dillon_near', #nft #pfp #mintbase #community #capybara
        'monzaNFT', #nft #community #nearforest #cm #community #marketing #near_at_night #xspace #space
        'OpenForest_', #rwa #onchain #carbon #consensuslayer #layer #defi #stake #lending #bonds #token
        'edgevideoai', #stream #space #video #fast #revenue #edge #ai
        'pironidi', #didier #defi #dev #growth #founder #pikespeak #ref #reffinance
        'NEARChainStatus', #onchain #data #validator #infra #community #news #devrel #updates #status
        'marrowng', #metapool #marketing #founder #community #latam #español
        'noahmajor1776', #nono #nearmaxi #content #creator #community #news #dev
        'NEAR_Arabic', #nation #arab #language #community
        'EsNearEs', #español #latam #noticias #news #community
        'NearPositive', #community #news
        'Near_Colombia', #latam #nation #español #colombia #news #community
        'MITTE_gg', #nft #dapp #nftmarketplace #trade #trading
        'EvgenSkydan', #ukraine #ucrania #nearua #nearuaguild #neardc #explorer #news #dev #onchain #community
        'jjyuannear', #jerry #yuannear #nearusa #usa #banyan #founder #news #dev #devrel #community
        'Banyan_NEAR', #build #dev #project #banyan #nearprotocol #develop
        'SourceDegen', #degen #community
        'rendal73', #degen #community
        'n0trdame', #degen #community
        'here_wallet', #wallet #competition #hot #telegram
        'cosmos', #cosmos #cosmossdk #ibc #consensuslayer #layer #atom
        'axelar', #bridge #axelar #token
        'EvmosOrg', #evm #network #evmos
        'osmosiszone', #osmosis #cosmos #atom
        'near_malaysia', #nation #community #malaysia #malasia #asia #community
        'ekosubagyo', #maxone #metapool #community #ambassador
        'alannetwork_', #metapool #latam #openweb #dev
        'swisshustler', #nearprotocol #swiss #nearfoundation
        'Mikikin8', #defi #founder #dev #defishards #shards 
        'DeFiShardsxyz', #defi #sharding #shards defishards #nft #docs #liquid #stake
        'mraltantutar', #nearprotocol #nearfoundation #georgia #founder #dev #chain #chainabstracted #signatures
        'aescobarindo', #escobar #reffinance #ref #dapdap #dex #dev #marketing #community #founder #playember
        'chronear', #dev #build #chain #chainabstraction #abstraction #signatures #chainsig
        'NearIndia', #india #asia #nation #community #dev #news
        'yuvalxyz', #magma #lava #lavanet #marketing #bd #community #infra #data
        'yaircleper', #founder #lava #lavanet #magma #cleper
        'thelittlesnft', #nft #thelittles #nfts #design
        'bodega_web3', #bodega #community #game #dev #collectibles #nft #nfts
        'AlexSkidanov', #founder #nearfounder #nearprotocol #dev #news #community
        'NearTinkerUnion', #nft #nfts #collection
        '0xshadowbrown', #chain #chainabstractor #chainasbtraction #abstraction #chainsig #chainsignatures #signature #dev #build
        'quadron3stat3', #founder #news #nearweek #community #nearfoundation #nearprotocol
        'joeespano_', #joe #sharddog #dev #devrel #learn #tutorials #neardevhub
        'Freol', #dev #learn #build #docs #nearprotocol #neardevhub #developer
        'ChrisDoNEARvan', #founder #dev #learn #devrel #neardevhub #devhub #nearfoundation
        'NearMultiverse', #metapool #marketing #community #latam #ecuador
        'BrazillianCare', #brazil #metapool #latam #growth #community #founder
        'waxnear', #wax #community #news #influncer
        'Nearbigfinance', #news #community #defi
        'NearVietnamHub', #nation #news #vietnam #asia #community
        'NearKoreaHub', #nation #news #korea #southkorea #asia #community
        'near_intern', #intern #degen #community
        'lauranear', #nearprotocol #nearfoundation #product
        'NameSkyApp', #dapp #domains #neardomains #dotnear #.near #accounts #wallets #buy #sell #trade
        'ready_layer_one', #metaverse #build #community #nft #content #sharddog
        'jarednotjerry1', #sharddog #nft #dev #community #build
        'ElCafeCartel', #dapp #game #nft #dev #build
        'SecretSkellies', #nft #collection #art #nfts #build
        'ASAC_NFT', #antisocial #apes #club #nft #nfts #art #build #collection
        'AlexAuroraDev', #founder #ceo #aurora #dev
        'near_family', #family #news #community #nft #trade #meme
        'CalimeroNetwork', #calimero #network #privacy #data #chat #build #dev #asia #ownership
        'PagodaPlatform', #pagoda #nearprotocol #nearfoundation #infra #dev #build
        'NEARBalkan', #nation #news #community #balkans #europe #easteurope #news #balkans 
        'BitteProtocol', #bitte #wallet #ai #competition
        'NEAR__SF', #siliconvalley #silicon #valley #sanfrancisco #san #francisco #usa #america #devs #news #community #nation
        'DeAlmeidaDavid', #validator #ai #onchain #fetchai #panda #pandateam
        'NEAR_China', #china #nation #asia #community
        'NEARProtocolJP', #japan #nearjapan #asia #dev #news #community
        'SweatEconomy', #sweat #economy #walktoearn #sweattoern #dev #build
        'LearnNear', #learn #dev #build #educate
        'near_insider', #news #learn #community #build #data #onchain
        'awesome_near', #news #data #dapps #dappsradar #catalogue #nearprotocol #docs #community
        'LinearProtocol', #layer #omni #chain #liquid #stake #restake #abstracted #chainabstraction #signatures
        'Cameron_Dennis_', #news #influencer #cameron #dev #thebafnetwork #nearprotocol #community
        'ParasHQ', #nft #marketplace #nfts #paras #trade #buy #sell
        'NEAR_Blockchain', #news #community #trend #influencer
        'nekotoken_xyz', #meme #memecoins #neko #token
        'NearFrancais', #french #nation #europe #francais #frances #news #community
        'billybones1_' #founder #influencer #news #build #dev
        'FewandFarNFT', #nft #nfts #community #art
        'NEARFoundation', #nearfoundation #nearprotocol #news #community #dao

    ]

    for account in accounts:
        logging.info(f"Fetching tweets for account: {account}")
        current_date = end_date

        # Crear un directorio de datos para cada cuenta
        account_data_directory = os.path.join(config['data_directory'], account)
        ensure_data_directory(account_data_directory)

        api_calls_count = 0
        records_fetched = 0
        all_tweets = []

        while current_date >= start_date:
            success = False
            attempts = 0

            while not success and attempts < config['max_retries']:
                iteration_start_date = current_date - timedelta(days=days_per_iteration)
                day_before = max(iteration_start_date, start_date - timedelta(days=1))

                # Crear el query para la cuenta actual
                query = create_tweet_query(account, day_before, current_date)
                print(query)
                request_body = {"query": query, "count": config['tweets_per_request']}

                try:
                    response = requests.post(
                        config['api_endpoint'],
                        json=request_body,
                        headers=config['headers'],
                        timeout=config['request_timeout']
                    )
                    api_calls_count += 1

                    if response.status_code == 200:
                        response_data = response.json()
                        if response_data and 'data' in response_data and response_data['data'] is not None:
                            tweets = response_data['data']
                            all_tweets.extend(tweets)
                            num_tweets = len(tweets)
                            records_fetched += num_tweets
                            logging.info(f"Fetched {num_tweets} tweets for {account} from {day_before} to {current_date}.")
                            success = True
                        else:
                            logging.warning(f"No tweets fetched for {account} from {day_before} to {current_date}. Retrying after delay...")
                            time.sleep(config['request_delay'])
                            attempts += 1
                    elif response.status_code == 429 or response.status_code == 500:
                        if response.status_code == 429:
                            logging.warning("Rate-limited. Retrying after delay...")
                            time.sleep(exponential_backoff(attempts, base=config['retry_delay']))
                            attempts += 1
                        elif response.status_code == 500:
                            logging.warning("500 Error. Retrying after delay...")
                            time.sleep(exponential_backoff(attempts, base=config['retry_delay']))
                            attempts += 1
                    else:
                        logging.error(f"Failed to fetch tweets: {response.status_code}")
                        break

                except requests.exceptions.RequestException as e:
                    logging.error(f"Request failed: {e}")
                    time.sleep(exponential_backoff(attempts, base=config['retry_delay']))
                    attempts += 1

            if not success:
                logging.error(f"Failed after {attempts} attempts for {account} from {day_before} to {current_date}")

            # Guardar el estado si es necesario
            save_state({'current_date': current_date.strftime('%Y-%m-%d'), 'account': account}, api_calls_count, records_fetched, all_tweets)
            current_date -= timedelta(days=days_per_iteration)
            time.sleep(config['request_delay'])

        # Guardar todos los tweets de la cuenta actual
        save_all_tweets(all_tweets, account_data_directory, f"from:{account}")

        logging.info(f"Finished fetching tweets for account: {account}. Total API calls: {api_calls_count}. Total records fetched: {records_fetched}")

if __name__ == "__main__":
    load_dotenv()
    config = load_config()
    setup_logging(config['log_level'], config['log_format'])
    fetch_tweets(config)