-- 一件商品 --
DROP DATABASE ec_spider;
CREATE DATABASE ec_spider;

use ec_spider;

CREATE TABLE commodity(
	-- Mysql 所能接受最大长度为767 --
	item_url_md5 CHAR(32) PRIMARY KEY, -- 商品url哈希码，作为主键 --
	item_url TEXT NOT NULL, 	-- 商品url --
	item_title VARCHAR(250) NOT NULL,	-- 商品标题 --
	item_name VARCHAR(250) NOT NULL,	-- 商品名称 --
	item_type VARCHAR(250),		-- 产品类别 --
	keyword varchar(250) NOT NULL,  -- 通过什么关键字搜到该商品的？ --
	store_name VARCHAR(250) NOT NULL,	-- 店铺名 --
	store_url TEXT NOT NULL,		-- 店铺URL --
	access_num INT NOT NULL,			-- 近期访问次数，定时清空 --
    FOREIGN KEY(keyword) REFERENCES keyword(keyword)
) default charset = utf8;


-- 商品规格详情 --
CREATE TABLE Item(
	item_url_md5 CHAR(32) NOT NULL, -- 唯一标识一个商品 --
	item_url TEXT NOT NULL,		-- 网址 --
	data_begin_time DOUBLE NOT NULL,		-- 该价格开始日期 --
	data_latest_time DOUBLE NOT NULL,        -- 最近访问日期 --
	data_end_time DOUBLE NOT NULL,		-- 该价格结束日期 --
	item_price DOUBLE NOT NULL,		-- 单价 --
	plus_price DOUBLE,		-- plus会员价格 --
	ticket VARCHAR(250),		-- 满减券 --
	inventory INT,		-- 库存(可能遇见有价无货的状态, 可能进入网页并未选择规格，可能产品下架) --
	sales_amount INT,	-- 销量 --
	transport_fare DOUBLE,		-- 运费 --
	all_specification TEXT,	-- 以下可选字段信息的并集 --
	spec1 TEXT,		-- 可选字段1. 大类，一般是型号/颜色等（可能显示的是图片） --
	spec2 TEXT,		-- 可选字段2. 大类中的小类，如某种特定颜色的尺码/容量 --
	spec3 TEXT,		-- 可选字段3 --
	spec4 TEXT,		-- 可选字段4 --
	spec5 TEXT,		-- 可选字段5 --
	spec_other TEXT,	-- 其余可选字段合并 --
    FOREIGN KEY(item_url_md5) REFERENCES commodity(item_url_md5),
	PRIMARY KEY(item_url_md5 ASC, data_begin_time DESC) -- 默认按时间降序排列 --
) default charset = utf8;


CREATE TABLE keyword(
	keyword VARCHAR(250) PRIMARY KEY, -- 搜索关键词 --
	update_time DOUBLE NOT NULL	-- 该关键词更新日期 --
) default charset = utf8;








